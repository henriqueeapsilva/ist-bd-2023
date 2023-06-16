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


def is_price(value):
    size = len(value)
    for i in range(size):
        if not value[i].isdigit() and value[i] not in ('.', ','):
            return False
    return True


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
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


@app.route("/products/register", methods=("GET", "POST"))
def product_register():
    """Register a new product."""

    if request.method == "POST":
        error = None

        SKU = request.form["SKU"]
        if not SKU:
            error = "SKU is required."
        else:
            if len(SKU) > 25:
                error = "SKU is required to be atmost 25 characters long."

        name = request.form["name"]
        if not name:
            error = "Name is required."
        else:
            if len(name) > 200:
                error = "Name is required to be atmost 200 characters long."

        desc = request.form["description"]

        price = request.form["price"]
        if not price:
            error = "Price is required."
        else:
            if not is_price(price):
                error = "Price isn't valid."
            elif len(price) > 11:
                error = "Price must have atmost 10 digits."

        EAN = request.form["EAN"]
        if EAN == "":
            EAN = 0
        if EAN is not None:
            if not EAN.isnumeric():
                error = "EAN is required to be numeric."
            elif len(EAN) > 13:
                error = "EAN is required to be atmost 13 digits long."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    sku_exists = cur.execute(
                        """
                        SELECT COUNT(*) as sku_exists
                        FROM product
                        WHERE SKU = %(SKU)s;
                        """,
                        {"SKU": SKU},
                    ).fetchone()
                    ean_exists = cur.execute(
                        """
                        SELECT COUNT(*) as ean_exists
                        FROM product
                        WHERE ean = %(ean)s;
                        """,
                        {"ean": EAN},
                    ).fetchone()
                    if sku_exists[0] == 1:
                        error = "There is already a product with that SKU."
                        flash(error)
                        return redirect(url_for("product_register"))
                    if ean_exists[0] == 1:
                        error = "There is already a product with that ean."
                        flash(error)
                        return redirect(url_for("product_register"))
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
        if price is not None:
            if not is_price(price):
                error = "Price isn't valid."
            elif len(price) > 11:
                error = "Price must have atmost 10 digits."

        desc = request.form["description"]

        if not price and not desc:
            error = "Atleast one of price or description is required."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    if price is not None:
                        cur.execute(
                            """
                            UPDATE product
                            SET price = %(price)s
                            WHERE SKU = %(product_sku)s;
                            """,
                            {"product_sku": product_sku, "price": price},
                        )
                    if desc is not None:
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


@app.route("/suppliers/register", methods=("GET", "POST"))
def supplier_register():
    """Register a new supplier."""

    if request.method == "POST":
        error = None

        TIN = request.form["TIN"]
        if not TIN:
            error = "TIN is required."
        else:
            if len(TIN) > 20:
                error = "TIN is required to be atmost 20 characters long."

        name = request.form["name"]
        if name is not None:
            if len(name) > 200:
                error = "Name is required to be atmost 200 characters long."

        address = request.form["address"]
        if address is not None:
            if len(address) > 255:
                error = "Address is required to be atmost 255 characters long."

        SKU = request.form["SKU"]
        if not SKU:
            error = "SKU is required."
        else:
            if len(SKU) > 25:
                error = "SKU is required to be atmost 25 characters long."

        date = request.form["date"]

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    tin_exists = cur.execute(
                        """
                        SELECT COUNT(*) as tin_exists
                        FROM supplier
                        WHERE TIN = %(TIN)s;
                        """,
                        {"TIN": TIN},
                    ).fetchone()
                    sku_exists = cur.execute(
                        """
                        SELECT COUNT(*) as sku_exists
                        FROM product
                        WHERE SKU = %(SKU)s;
                        """,
                        {"SKU": SKU},
                    ).fetchone()
                    if tin_exists[0] == 1:
                        error = "There is already a supplier with that TIN."
                        flash(error)
                        return redirect(url_for("supplier_register"))
                    if sku_exists[0] == 0:
                        error = "There isn't a product with that SKU."
                        flash(error)
                        return redirect(url_for("supplier_register"))
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
                DELETE FROM delivery
                WHERE TIN = %(supplier_tin)s;
                """,
                {"supplier_tin": supplier_tin},
            )
            cur.execute(
                """
                DELETE FROM supplier
                WHERE TIN = %(supplier_tin)s;
                """,
                {"supplier_tin": supplier_tin},
            )
        conn.commit()
    return redirect(url_for("supplier_index"))


@app.route("/suppliers/<tin>/update", methods=("GET", ))
def supplier_info(tin):
    """Show supplier information."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            supplier = cur.execute(
                """
                SELECT TIN, name, address, SKU, date
                FROM supplier
                WHERE TIN = %(tin)s;
                """,
                {"tin": tin},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    return render_template("suppliers/update.html", supplier=supplier)


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
            ).fetchall()

    return render_template("customers/index.html", customers=customers)


@app.route("/customers/register", methods=("GET", "POST"))
def customer_register():
    """Register a new customer."""

    if request.method == "POST":
        error = None

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
        if phone is not None:
            if len(phone) > 15:
                error = "Phone is required to be atmost 15 characters long."

        address = request.form["address"]
        if address is not None:
            if len(address) > 255:
                error = "Address is required to be atmost 255 characters long."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    max_cust_no = cur.execute(
                        """
                        SELECT cust_no FROM customer
                        WHERE cust_no >= ALL(
                            SELECT cust_no FROM customer);
                        """,
                    ).fetchone()
                    email_exists = cur.execute(
                        """
                        SELECT COUNT(*) as email_exists
                        FROM customer
                        WHERE email = %(email)s;
                        """,
                        {"email": email},
                    ).fetchone()
                    if email_exists[0] == 1:
                        error = "There is already a customer with that email."
                        flash(error)
                        return redirect(url_for("customer_register"))
                    cur.execute(
                        """
                        INSERT INTO customer VALUES (%(cust_no)s, %(name)s, %(email)s, 
                            %(phone)s, %(address)s);
                        """,
                        {"cust_no": max_cust_no[0]+1, "name": name, "email": email, "phone": phone, "address": address},
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
                """DELETE FROM process
                WHERE order_no IN (
                    SELECT order_no FROM orders
                    WHERE cust_no = %(cust_no)s);
                """,
                {"cust_no": cust_no},
            )
            cur.execute(
                """DELETE FROM contains
                WHERE order_no IN (
                    SELECT order_no FROM orders
                    WHERE cust_no = %(cust_no)s);
                """,
                {"cust_no": cust_no},
            )
            cur.execute(
                """
                DELETE FROM pay
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            )
            cur.execute(
                """
                DELETE FROM orders
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            )
            cur.execute(
                """
                DELETE FROM customer
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            )
            conn.commit()
    return redirect(url_for("customer_index"))


@app.route("/customers/<cust_no>/update", methods=("GET", ))
def customer_info(cust_no):
    """Show customer information."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            customer = cur.execute(
                """
                SELECT cust_no, name, email, phone, address
                FROM customer
                WHERE cust_no = %(cust_no)s;
                """,
                {"cust_no": cust_no},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    return render_template("customers/update.html", customer=customer)


@app.route("/orders", methods=("GET",))
def orders_index():
    """Show all the orders."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            orders = cur.execute(
                """
                SELECT order_no, cust_no, date
                FROM orders
                ORDER BY order_no ASC;
                """,
            ).fetchall()

    return render_template("orders/index.html", orders=orders)


@app.route("/orders/register", methods=("GET", "POST"))
def place_order():
    """Place a new order."""

    if request.method == "POST":
        error = None

        cust_no = request.form["cust_no"]
        if not cust_no:
            error = "Customer number is required."
        else:
            if not cust_no.isnumeric():
                error = "Customer number is required to be an integer."

        date = request.form["date"]
        if not date:
            error = "Date is required."

        first_sku = request.form["sku"]
        if not first_sku:
            error = "New order is required to have atleast one product."
        else:
            if len(first_sku) > 25:
                error = "SKU is required to be atmost 25 characters long."

        qty = request.form["qty"]
        if not qty:
            error = "Quantity is required."
        else:
            if not qty.isnumeric() or int(qty) <= 0:
                error = "Quantity is required to be a positive integer."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    max_order_no = cur.execute(
                        """
                        SELECT order_no FROM orders
                        WHERE order_no >= ALL(
                            SELECT order_no FROM orders);
                        """,
                    ).fetchone()
                    client_exists = cur.execute(
                        """
                        SELECT COUNT(*) as client_exists
                        FROM customer
                        WHERE cust_no = %(cust_no)s;
                        """,
                        {"cust_no": cust_no},
                    ).fetchone()
                    product_exists = cur.execute(
                        """
                        SELECT COUNT(*) as product_exists
                        FROM product
                        WHERE SKU = %(sku)s;
                        """,
                        {"sku": first_sku},
                    ).fetchone()
                    if client_exists[0] == 0:
                        error = "There isn't a customer with that number."
                        flash(error)
                        return redirect(url_for("place_order"))
                    if product_exists[0] == 0:
                        error = "There isn't a product with that SKU."
                        flash(error)
                        return redirect(url_for("place_order"))
                    cur.execute(
                        """
                        INSERT INTO orders VALUES (%(new_order_no)s, %(cust_no)s, %(date)s);
                        """,
                        {"new_order_no": max_order_no[0]+1, "cust_no": cust_no, "date": date},
                    )
                    cur.execute(
                        """
                        INSERT INTO contains VALUES (%(new_order_no)s, %(sku)s, %(qty)s);
                        """,
                        {"new_order_no": max_order_no[0]+1, "sku": first_sku, "qty": qty},
                    )
                conn.commit()
            return redirect(url_for("orders_index"))

    return render_template("orders/register.html")


@app.route("/orders/<order_no>/addproduct", methods=("GET", "POST"))
def add_product(order_no):
    """Add a new product to an existing order."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            payed = cur.execute(
                """
                SELECT COUNT(*) as payed
                FROM pay
                WHERE order_no = %(order_no)s;
                """,
                {"order_no": order_no},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    if payed[0] == 1:
        error = "Cannot add products to an order that is already payed."
        flash(error)
        return redirect(url_for("order_info", order_no=order_no))

    if request.method == "POST":
        error = None

        sku = request.form["sku"]
        if not sku:
            error = "Product SKU is required."
        else:
            if len(sku) > 25:
                error = "SKU is required to be atmost 25 characters long."

        qty = request.form["qty"]
        if not qty:
            error = "Quantity is required."
        else:
            if not qty.isnumeric() or int(qty) <= 0:
                error = "Quantity is required to be a positive integer."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    product_exists = cur.execute(
                        """
                        SELECT COUNT(*) as product_exists
                        FROM product
                        WHERE SKU = %(sku)s;
                        """,
                        {"sku": sku},
                    ).fetchone()
                    if product_exists[0] == 0:
                        error = "There isn't a product with that SKU."
                        flash(error)
                        return redirect(url_for("add_product", order_no=order_no))
                    product_already_in_order = cur.execute(
                        """
                        SELECT COUNT(*) as product_already_in_order
                        FROM contains
                        WHERE SKU = %(sku)s AND order_no=%(order_no)s;
                        """,
                        {"sku": sku, "order_no": order_no},
                    ).fetchone()
                    if product_already_in_order[0] == 1:
                        cur.execute(
                            """
                            UPDATE contains SET qty = qty + %(qty)s
                            WHERE SKU = %(sku)s AND order_no=%(order_no)s;
                            """,
                            {"qty": qty, "sku": sku, "order_no": order_no},
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO contains VALUES (%(order_no)s, %(sku)s, %(qty)s);
                            """,
                            {"order_no": order_no, "sku": sku, "qty": qty},
                        )
                conn.commit()
            return redirect(url_for("order_info", order_no=order_no))

    return render_template("orders/addproduct.html", order_no=order_no)


@app.route("/orders/<order_no>/update", methods=("GET", ))
def order_info(order_no):
    """Show order information."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            order = cur.execute(
                """
                SELECT order_no, cust_no, date
                FROM orders
                WHERE order_no = %(order_no)s;
                """,
                {"order_no": order_no},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")
            products = cur.execute(
                """
                SELECT order_no, SKU, qty, name
                FROM contains JOIN product USING (SKU)
                WHERE order_no = %(order_no)s;
                """,
                {"order_no": order_no},
            ).fetchall()

    return render_template("orders/update.html", order=order, products=products)


@app.route("/orders/<order_no>/pay", methods=("GET", "POST"))
def pay_order(order_no):
    """Pay the order."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            payed = cur.execute(
                """
                SELECT COUNT(*) as payed
                FROM pay
                WHERE order_no = %(order_no)s;
                """,
                {"order_no": order_no},
            ).fetchone()
            order_totals = cur.execute(
                """
                SELECT COUNT(*) as total_products, SUM(qty) as total_qty, SUM(qty*price) as total_price
                FROM contains JOIN product USING (SKU)
                WHERE order_no = %(order_no)s;
                """,
                {"order_no": order_no},
            ).fetchone()
            log.debug(f"Found {cur.rowcount} rows.")

    if payed[0] == 1:
        error = "Order is already payed."
        flash(error)
        return redirect(url_for("order_info", order_no=order_no))

    if request.method == "POST":
        error = None

        payment_method = request.form["payment_method"]
        if not payment_method:
            error = "Payment method is required."
        else:
            if payment_method not in ("MBWay", "Multibanco", "Paypal", "Visa"):
                error = "Payment method is required to be one of those listed."

        cust_no_pay = request.form["cust_no_pay"]
        if not cust_no_pay:
            error = "The number of the customer who is going to pay is required."
        else:
            if not cust_no_pay.isnumeric():
                error = "Customer number is required to be an integer."

        if error is not None:
            flash(error)
        else:
            with pool.connection() as conn:
                with conn.cursor(row_factory=namedtuple_row) as cur:
                    cust_no_order = cur.execute(
                        """
                        SELECT cust_no FROM orders
                        WHERE order_no = %(order_no)s;
                        """,
                        {"order_no": order_no},
                    ).fetchone()
                    if cust_no_order[0] == int(cust_no_pay):
                        cur.execute(
                            """
                            INSERT INTO pay VALUES (%(order_no)s, %(cust_no)s);
                            """,
                            {"order_no": order_no, "cust_no": cust_no_pay},
                        )
                    else:
                        error = "An order must be payed by the client who placed it."
                        flash(error)
                conn.commit()
            return redirect(url_for("order_info", order_no=order_no))

    return render_template("orders/pay.html", order_totals=order_totals, order_no=order_no)


if __name__ == "__main__":
    app.run()
