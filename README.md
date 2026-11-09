# Smart Credit Ledger

A web-based credit ledger management system built using Python and FastAPI to manage customers, track credit transactions, record payments, and monitor outstanding balances.

## Features

Customer Management: Add and manage customer details.
Credit Management: Record and track customer credit.
Purchase Management: Maintain customer purchase records.
Payment Tracking: Record payments and monitor pending balances.
Customer Details: View individual customer transaction history.
Dashboard: Get an overview of customers and credit activity.

## Technologies Used

Programming Language: Python
Backend Framework: FastAPI
ASGI Server: Uvicorn
Database: SQLite
ORM: SQLAlchemy
Frontend: HTML, CSS
Templating Engine: Jinja2

## Project Structure


smart-credit-ledger/
│
├── main.py
├── database.py
├── models.py
├── schemas.py
├── requirements.txt
├── .gitignore
│
├── static/
│   └── style.css
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── customers.html
│   ├── add_customer.html
│   ├── customer_detail.html
│   ├── add_credit.html
│   ├── add_payment.html
│   ├── add_purchase.html
│   ├── products.html
│   └── store.html
│
└── README.md


## Installation and Setup

### 1. Clone the repository


git clone https://github.com/Akshara466/smart-credit-ledger.git
cd smart-credit-ledger

### 2. Create a virtual environment

python -m venv venv

### 3. Activate the virtual environment

venv\Scripts\activate

### 4. Install dependencies

pip install -r requirements.txt

### 5. Run the application

uvicorn main:app --reload

### 6. Open in your browser

- Application: http://127.0.0.1:8000
- API Documentation: http://127.0.0.1:8000/docs

## Author

Akshara Pasupuleti

GitHub: https://github.com/Akshara466
