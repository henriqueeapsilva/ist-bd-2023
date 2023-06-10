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

## SGBD configs
DB_HOST="db.tecnico.ulisboa.pt"
DB_USER="ist1102927" 
DB_DATABASE=DB_USER
DB_PASSWORD="pepas123"
DB_CONNECTION_STRING = "host=%s dbname=%s user=%s password=%s" % (DB_HOST, DB_DATABASE, DB_USER, DB_PASSWORD)

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

@app.route("/")
def homepage():
    try:
        return render_template("index.html")
    except Exception as e:
        return render_template("error_page.html", error=e)

@app.route("/products", methods=("GET",))
def products_index():
    """Show all the products."""

    with pool.connection() as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            products = cur.execute(
                """
                SELECT SKU, name, description, price, COALESCE(EAN, '-')
                FROM product
                ORDER BY SKU ASC;
                """,
                {},
            ).fetchall()

    return render_template("products/index.html", products=products)

@app.route("/suppliers", methods=("GET",))
def suppliers_index():
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

@app.route("/products/register", methods=("POST", ))
def product_register(product_SKU):
    """Register a new product."""

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
            return redirect(url_for("products_index"))

if __name__ == "__main__":
    app.run()