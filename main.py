
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from database import Base, SessionLocal, engine
from models import Customer, Credit, Product, Sale, SaleItem, Payment


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Credit Ledger")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def money(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def get_ledger(db: Session, customer_id: int):
    """Calculate a customer's total purchases, payments and balance."""

    legacy_credits = db.query(Credit).filter(
        Credit.customer_id == customer_id
    ).all()

    sales = db.query(Sale).filter(
        Sale.customer_id == customer_id
    ).all()

    payments = db.query(Payment).filter(
        Payment.customer_id == customer_id
    ).all()

    old_credit_total = sum(
        (money(c.amount) for c in legacy_credits), Decimal("0.00")
    )
    sales_total = sum(
        (money(s.total_amount) for s in sales), Decimal("0.00")
    )
    payment_total = sum(
        (money(p.amount) for p in payments), Decimal("0.00")
    )

    total_credit = old_credit_total + sales_total
    balance = total_credit - payment_total

    return {
        "legacy_credits": old_credit_total,
        "sales_total": sales_total,
        "total_credit": total_credit,
        "payment_total": payment_total,
        "balance": balance,
    }


def render(request, name, context=None, status_code=200):
    data = {"request": request}
    if context:
        data.update(context)
    return templates.TemplateResponse(
        request=request,
        name=name,
        context=data,
        status_code=status_code,
    )


def parse_date(value: str):
    try:
        return date.fromisoformat(value) if value else date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date.")


def parse_money(value: str):
    try:
        amount = Decimal(value).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=400, detail="Enter a valid amount.")

    if not amount.is_finite() or amount < 0:
        raise HTTPException(status_code=400, detail="Amount cannot be negative.")

    return amount


@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    sales = db.query(Sale).all()
    payments = db.query(Payment).all()
    legacy_credits = db.query(Credit).all()

    total_credit = sum(
        (money(c.amount) for c in legacy_credits), Decimal("0.00")
    ) + sum(
        (money(s.total_amount) for s in sales), Decimal("0.00")
    )

    total_payments = sum(
        (money(p.amount) for p in payments), Decimal("0.00")
    )

    recent_sales = (
        db.query(Sale)
        .options(joinedload(Sale.customer))
        .order_by(Sale.id.desc())
        .limit(5)
        .all()
    )

    recent_payments = (
        db.query(Payment)
        .options(joinedload(Payment.customer))
        .order_by(Payment.id.desc())
        .limit(5)
        .all()
    )

    balances = [
        get_ledger(db, customer.id)["balance"]
        for customer in customers
    ]

    return render(request, "index.html", {
        "customer_count": len(customers),
        "product_count": db.query(Product).filter(
            Product.is_available.is_(True)
        ).count(),
        "total_credit": total_credit,
        "total_payments": total_payments,
        "outstanding": sum(balances, Decimal("0.00")),
        "recent_sales": recent_sales,
        "recent_payments": recent_payments,
    })


@app.get("/customers")
def customers_page(
    request: Request,
    query: str = "",
    db: Session = Depends(get_db),
):
    q = db.query(Customer)

    if query.strip():
        term = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Customer.name.ilike(term),
                Customer.phone.ilike(term),
            )
        )

    customers = q.order_by(Customer.name).all()

    rows = []
    for customer in customers:
        ledger = get_ledger(db, customer.id)
        rows.append({
            "customer": customer,
            "balance": ledger["balance"],
            "total_credit": ledger["total_credit"],
            "payment_total": ledger["payment_total"],
        })

    return render(request, "customers.html", {
        "rows": rows,
        "query": query,
    })


@app.get("/add-customer")
def add_customer_page(request: Request):
    return render(request, "add_customer.html")


@app.post("/add-customer")
def save_customer(
    name: str = Form(...),
    phone: str = Form(""),
    village: str = Form(""),
    db: Session = Depends(get_db),
):
    name = name.strip()
    phone = phone.strip()
    village = village.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Customer name is required.")

    if phone:
        existing = db.query(Customer).filter(
            Customer.phone == phone
        ).first()
        if existing:
            return RedirectResponse(
                f"/customers/{existing.id}",
                status_code=303,
            )

    customer = Customer(name=name, phone=phone, village=village)
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return RedirectResponse(
        f"/customers/{customer.id}",
        status_code=303,
    )


@app.get("/customers/{customer_id}")
def customer_detail(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    ledger = get_ledger(db, customer_id)

    sales = (
        db.query(Sale)
        .options(joinedload(Sale.items))
        .filter(Sale.customer_id == customer_id)
        .order_by(Sale.sale_date.desc(), Sale.id.desc())
        .all()
    )

    payments = (
        db.query(Payment)
        .filter(Payment.customer_id == customer_id)
        .order_by(Payment.payment_date.desc(), Payment.id.desc())
        .all()
    )

    legacy_credits = (
        db.query(Credit)
        .filter(Credit.customer_id == customer_id)
        .all()
    )

    return render(request, "customer_detail.html", {
        "customer": customer,
        "ledger": ledger,
        "sales": sales,
        "payments": payments,
        "legacy_credits": legacy_credits,
    })


@app.get("/add-purchase")
def add_purchase_page(
    request: Request,
    customer_id: int | None = None,
    db: Session = Depends(get_db),
):
    customers = db.query(Customer).order_by(Customer.name).all()
    products = db.query(Product).filter(
        Product.is_available.is_(True),
        Product.stock > 0,
    ).order_by(Product.name).all()

    return render(request, "add_purchase.html", {
        "customers": customers,
        "products": products,
        "selected_customer_id": customer_id,
        "today": date.today().isoformat(),
    })


@app.post("/add-purchase")
def save_purchase(
    customer_id: int = Form(...),
    sale_date: str = Form(...),
    product_ids: list[int] = Form(...),
    quantities: list[int] = Form(...),
    paid_now: str = Form("0"),
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    if len(product_ids) != len(quantities) or not product_ids:
        raise HTTPException(status_code=400, detail="Select at least one item.")

    purchase_date = parse_date(sale_date)
    paid = parse_money(paid_now)

    if paid < 0:
        raise HTTPException(status_code=400, detail="Invalid payment.")

    lines = []
    total = Decimal("0.00")

    for product_id, quantity in zip(product_ids, quantities):
        if quantity < 1:
            raise HTTPException(status_code=400, detail="Quantity must be at least 1.")

        product = db.get(Product, product_id)
        if not product or not product.is_available:
            raise HTTPException(status_code=400, detail="A selected product is unavailable.")

        if quantity > product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock}",
            )

        unit_price = money(product.price)
        line_total = (unit_price * quantity).quantize(Decimal("0.01"))
        total += line_total

        lines.append({
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total,
        })

    if paid > total:
        raise HTTPException(
            status_code=400,
            detail="Payment cannot exceed the purchase total.",
        )

    sale = Sale(
        customer_id=customer_id,
        sale_date=purchase_date,
        total_amount=total,
    )
    db.add(sale)

    try:
        db.flush()

        for line in lines:
            product = line["product"]
            product.stock -= line["quantity"]

            db.add(SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                item_name=product.name,
                quantity=line["quantity"],
                unit_price=line["unit_price"],
                line_total=line["line_total"],
            ))

        if paid > 0:
            db.add(Payment(
                customer_id=customer_id,
                amount=paid,
                payment_date=purchase_date,
                notes=f"Payment for purchase #{sale.id}",
            ))

        db.commit()

    except Exception:
        db.rollback()
        raise

    return RedirectResponse(
        f"/customers/{customer_id}",
        status_code=303,
    )


@app.get("/add-payment")
def add_payment_page(
    request: Request,
    customer_id: int | None = None,
    db: Session = Depends(get_db),
):
    customers = db.query(Customer).order_by(Customer.name).all()

    return render(request, "add_payment.html", {
        "customers": customers,
        "selected_customer_id": customer_id,
        "today": date.today().isoformat(),
    })


@app.post("/add-payment")
def save_payment(
    customer_id: int = Form(...),
    amount: str = Form(...),
    payment_date: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")

    paid = parse_money(amount)
    if paid <= 0:
        raise HTTPException(status_code=400, detail="Payment must be greater than zero.")

    ledger = get_ledger(db, customer_id)
    if paid > ledger["balance"]:
        raise HTTPException(
            status_code=400,
            detail=f"Payment exceeds the outstanding balance of ₹{ledger['balance']}.",
        )

    payment = Payment(
        customer_id=customer_id,
        amount=paid,
        payment_date=parse_date(payment_date),
        notes=notes.strip(),
    )

    db.add(payment)
    db.commit()

    return RedirectResponse(
        f"/customers/{customer_id}",
        status_code=303,
    )


@app.get("/products")
def products_page(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.name).all()
    return render(request, "products.html", {"products": products})


@app.post("/products/add")
def add_product(
    name: str = Form(...),
    description: str = Form(""),
    price: str = Form(...),
    stock: int = Form(...),
    unit: str = Form("piece"),
    db: Session = Depends(get_db),
):
    name = name.strip()
    unit = unit.strip() or "piece"
    amount = parse_money(price)

    if not name:
        raise HTTPException(status_code=400, detail="Product name is required.")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Price must be greater than zero.")
    if stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot be negative.")

    product = Product(
        name=name,
        description=description.strip(),
        price=amount,
        stock=stock,
        unit=unit,
        is_available=True,
    )
    db.add(product)
    db.commit()

    return RedirectResponse("/products", status_code=303)


@app.post("/products/{product_id}/update")
def update_product(
    product_id: int,
    price: str = Form(...),
    stock: int = Form(...),
    is_available: str = Form(""),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    amount = parse_money(price)
    if amount <= 0 or stock < 0:
        raise HTTPException(status_code=400, detail="Invalid price or stock.")

    product.price = amount
    product.stock = stock
    product.is_available = is_available == "yes"

    db.commit()
    return RedirectResponse("/products", status_code=303)


@app.get("/store")
def public_store(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).filter(
        Product.is_available.is_(True),
        Product.stock > 0,
    ).order_by(Product.name).all()

    return render(request, "store.html", {"products": products})


@app.get("/health")
def health():
    return {"status": "ok", "application": "Smart Credit Ledger"}
