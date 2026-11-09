
from datetime import date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Float,
)
from sqlalchemy.orm import relationship

from database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True, index=True)
    village = Column(String, nullable=True)

    sales = relationship("Sale", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")


# Kept compatible with your original credits table.
class Credit(Base):
    __tablename__ = "credits"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    item = Column(String, nullable=False)
    amount = Column(Float, nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, default="", nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    unit = Column(String, default="piece", nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    sale_date = Column(Date, default=date.today, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)

    customer = relationship("Customer", back_populates="sales")
    items = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
    )


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(
        Integer,
        ForeignKey("sales.id"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
    )

    # Snapshot fields preserve the original purchase details
    # even if a product's name or price changes later.
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    sale = relationship("Sale", back_populates="items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer,
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    amount = Column(Numeric(12, 2), nullable=False)
    payment_date = Column(Date, default=date.today, nullable=False)
    notes = Column(String, default="", nullable=False)

    customer = relationship("Customer", back_populates="payments")
