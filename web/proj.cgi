#!/usr/bin/python3
import os
from logging.config import dictConfig

import psycopg
from flask import flash
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from psycopg.rows import namedtuple_row
from psycopg_pool import ConnectionPool


# postgres://{user}:{password}@{hostname}:{port}/{database-name}
DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://db:db@postgres/db")

pool = ConnectionPool(conninfo=DATABASE_URL)
# the pool starts connecting immediately.

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - %(funcName)20s(): %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)
log = app.logger

@app.route("/", methods=("GET",))
def homepage():
    try:
        return render_template("home_page.html")
    except Exception as e:
        return render_template("error_page.html", error=e)


@app.route("/products", methods=("GET",))
def product_index():
    """Show all the products."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            products = cur.execute(
                """
                SELECT SKU, name, description, price, COALESCE(EAN, 0)
                FROM product
                ORDER BY SKU ASC;
                """,
                {},
            ).fetchall()

    return render_template("products/index.html", products=products)


@app.route("/suppliers", methods=("GET",))
def supplier_index():
    """Show all the suppliers."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            suppliers = cur.execute(
                """
                SELECT TIN, name, address, SKU
                FROM supplier
                ORDER BY TIN ASC;
                """,
                {},
            ).fetchall()

    return render_template("suppliers/index.html", suppliers=suppliers)


@app.route("/products/register", methods=("GET", "POST"))
def product_register():
    """Register a new product."""

    if request.method == "POST":
        error = None

        SKU = request.form["SKU"]
        if not SKU:
            error = "SKU is required."
            if not SKU.isalnum():
                error = "SKU is required to be alphanumeric."
            elif len(SKU) > 25:
                error = "SKU is required to be atmost 25 characters long."

        name = request.form["name"]
        if not name:
            error = "Name is required."
            if not name.isalnum():
                error = "Name is required to be alphanumeric."
            elif len(name) > 200:
                error = "Name is required to be atmost 200 characters long."

        desc = request.form["description"]

        price = request.form["price"]
        if not price:
            error = "Price is required."
            if not price.isnumeric():
                error = "Price is required to be numeric."

        EAN = request.form["EAN"]

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        """
                        INSERT INTO product VALUES (%(SKU)s, %(name)s, %(desc)s, 
                            %(price)s, %(EAN)s);
                        """,
                        {"SKU": SKU, "name": name, "desc": desc, "price": price, "EAN": EAN},
                    )
                conn.commit()
            return redirect(url_for("product_index"))
    
    return render_template("products/register.html")


@app.route("/products/<product_sku>/delete", methods=("POST",))
def product_delete(product_sku):
    """Delete the product."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                UPDATE supplier SET SKU = NULL
                WHERE SKU = %(product_sku)s;
                """,
                {"product_sku": product_sku},
            )
            cur.execute(
                """
                DELETE FROM contains
                WHERE SKU = %(product_sku)s;
                """,
                {"product_sku": product_sku},
            )
            cur.execute(
                """
                DELETE FROM product
                WHERE SKU = %(product_sku)s;
                """,
                {"product_sku": product_sku},
            )
        conn.commit()
    return redirect(url_for("product_index"))


@app.route("/suppliers/register", methods=("GET", "POST"))
def supplier_register():
    """Register a new supplier."""

    if request.method == "POST":
        error = None

        TIN = request.form["TIN"]
        if not TIN:
            error = "TIN is required."
            if not SKU.isalnum():
                error = "TIN is required to be alphanumeric."
            elif len(STIN) > 20:
                error = "TIN is required to be atmost 20 characters long."

        name = request.form["name"]
        if name is not NULL:
            if not name.isalnum():
                error = "Name is required to be alphanumeric."
            elif len(name) > 200:
                error = "Name is required to be atmost 200 characters long."

        address = request.form["address"]
        if address is not NULL:
            if len(address) > 255:
                error = "Address is required to be atmost 255 characters long."

        SKU = request.form["SKU"]
        if not SKU:
            error = "SKU is required."
            if not SKU.isalnum():
                error = "SKU is required to be alphanumeric."
            elif len(SKU) > 25:
                error = "SKU is required to be atmost 25 characters long."
        
        date = request.form["date"]
        if date is not NULL:
            if len(date) != 10:
                error = "Date is required to be a valid date in format YYYY-MM-DD."
            if int(date[0:4]) < 0 or date[4] != "-" or date[5:7] not in range(1,13) or date[7] != "-" or date[8:10] not in (1,32):
                error = "Date is required to be a valid date in format YYYY-MM-DD."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        """
                        INSERT INTO supplier VALUES (%(TIN)s, %(name)s, %(address)s, 
                            %(SKU)s, %(date)s);
                        """,
                        {"TIN": TIN, "name": name, "address": address, "SKU": SKU, "date": date},
                    )
                conn.commit()
            return redirect(url_for("supplier_index"))
    
    return render_template("suppliers/register.html")


@app.route("/supplier/<supplier_tin>/delete", methods=("POST",))
def supplier_delete(supplier_tin):
    """Delete the supplier."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                DELETE FROM supplier
                WHERE TIN = %(supplier_tin)s;
                """,
                {"supplier_tin": supplier_tin},
            )
        conn.commit()
    return redirect(url_for("supplier_index"))


@app.route("/products/<product_sku>/update", methods=("GET", "POST"))
def product_update(product_sku):
    """Update the product price or description."""
    
    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            product = cur.execute(
                """
                SELECT SKU, name, description, price
                FROM product
                WHERE SKU = %(product_sku)s;
                """,
                {"product_sku": product_sku},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    if request.method == "POST":
        error = None
        
        price = request.form["price"]
        if price is not NULL:
            if not price.isnumeric():
                error = "Price is required to be numeric."
        
        desc = request.form["description"]
        
        if not price and not desc:
            error = "Atleast one of price or description is required."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    if price is not NULL:
                        cur.execute(
                            """
                            UPDATE product
                            SET price = %(price)s
                            WHERE SKU = %(product_sku)s;
                            """,
                            {"product_sku": product_sku, "price": price},
                        )
                    if desc is not NULL:
                        cur.execute(
                            """
                            UPDATE product
                            SET description = %(desc)s
                            WHERE SKU = %(product_sku)s;
                            """,
                            {"product_sku": product_sku, "desc": desc},
                        )
                conn.commit()
            return redirect(url_for("product_index"))

    return render_template("products/update.html", product=product)


@app.route("/customers", methods=("GET",))
def customer_index():
    """Show all the customers."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            customers = cur.execute(
                """
                SELECT cust_no, name, email, phone, address
                FROM customer
                ORDER BY cust_no ASC;
                """,
                {},
            ).fetchall()

    return render_template("customers/index.html", customers=customers)


@app.route("/customers/register", methods=("GET", "POST"))
def customer_register():
    """Register a new customer."""

    if request.method == "POST":
        error = None

        cust_no = request.form["cust_no"]
        if not cust_no:
            error = "Customer number is required."
            if not cust_no.isnumeric():
                error = "Customer number is required to be an integer."
        
        name = request.form["name"]
        if not name:
            error = "Name is required."
            if not name.isalpha():
                error = "Name is required to be alphabetic."
            elif len(name) > 80:
                error = "Name is required to be atmost 80 characters long."
        
        email = request.form["email"]
        if not email:
            error = "Email is required."
            if len(email) > 254:
                error = "Email is required to be atmost 254 characters long."
        
        phone = request.form["phone"]
        if phone is not NULL:
            if len(phone) > 15:
                error = "Phone is required to be atmost 15 characters long."
        
        address = request.form["address"]
        if address is not NULL:
            if len(address) > 255:
                error = "Address is required to be atmost 255 characters long."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cur.execute(
                        """
                        INSERT INTO customer VALUES (%(cust_no)s, %(name)s, %(email)s, 
                            %(phone)s, %(address)s);
                        """,
                        {"cust_no": cust_no, "name": name, "email": email, "phone": phone, "address": address},
                    )
                conn.commit()
            return redirect(url_for("customer_index"))
    
    return render_template("customers/register.html")


@app.route("/customers/<cust_no>/delete", methods=("POST",))
def customer_delete(cust_no):
    """Delete the customer."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                DELETE FROM customer
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            )
        conn.commit()
    return redirect(url_for("customer_index"))


if __name__ == "__main__":
    app.run()