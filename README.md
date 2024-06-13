# Database Management and Web Application Project
### Overview

This project involves the design and implementation of a database schema, including data loading, integrity constraints, SQL queries, views, web application development, OLAP queries, and index optimization. The database system is designed to manage orders, customers, employees, products, and other related entities. A web application is also developed to facilitate various operations such as registering products and suppliers, managing orders, and simulating payments.

## Sections

#### 1. Loading the Database

The database schema is presented in Annex A. The data loading process ensures consistent data entry to produce non-empty results for the provided SQL and OLAP queries. Addresses are formatted in the Portuguese style, ending with a postal code in the format XXXX-XXX followed by the locality. Data can be loaded using various methods such as manual entry, Excel sheets, SQL scripts, or Python scripts.
#### 2. Integrity Constraints

Several integrity constraints are implemented to ensure data consistency and integrity:

    RI-1: No employee can be younger than 18 years old.
    RI-2: A 'Workplace' must be either an 'Office' or a 'Warehouse', but not both.
    RI-3: An 'Order' must be present in 'Contains'.

These constraints are implemented using SQL procedural extensions such as Stored Procedures and Triggers, except where simpler mechanisms are sufficient. The use of ON DELETE CASCADE and ON UPDATE CASCADE is prohibited.

#### 3. SQL Queries

Several SQL queries are provided to retrieve specific information from the database:

    The number and name of the customer(s) with the highest total value of paid orders.
    The names of employees who processed orders on every day in 2022 when orders were placed.
    The number of orders made but not paid for each month in 2022.

#### 4. Views

A view is created to summarize important information about product sales, combining data from different tables. The view schema is as follows:

    product_sales(sku, order_no, qty, total_price, year, month, day_of_month, day_of_week, city)

The attributes in the view correspond to primary keys, quantities, prices, dates, and customer addresses from various tables.
#### 5. Web Application Development

A prototype web application is developed using Python CGI scripts and HTML pages. The application allows users to:

    Register and remove products and suppliers
    Update product prices and descriptions
    Register and remove customers
    Place orders
    Simulate order payments

The application ensures security by preventing SQL injection attacks and maintains atomicity of database operations using transactions. The application is hosted on the sigma server of IST.
#### 6. OLAP Queries

Using the previously defined view, two OLAP queries are written:

    Quantities and total sales values for each product in 2022, by city, month, day of the month, and day of the week.
    The average daily sales value of all products in 2022, by month and day of the week.

These queries use SQL ROLLUP, CUBE, GROUPING SETS, or UNION of GROUP BY clauses.
#### 7. Indexes

Indexes are created to optimize query performance. For each provided query, appropriate indexes are suggested with explanations:

    Query 6.1:
        Index on orders(date)
        Index on product(price)
        Index on contains(order_no, SKU)
    Query 6.2:
        Index on product(name)
        Composite index on contains(order_no, SKU)

These indexes are designed to improve join operations and filtering conditions, especially when dealing with large datasets.

### How to Run

    Database Setup:
        Load the database schema and data using the provided scripts.
        Implement the integrity constraints using SQL extensions.

    Web Application:
        Deploy the Python CGI scripts and HTML pages on the sigma server.
        Ensure the application is accessible and functional for performing the specified operations.

    OLAP and SQL Queries:
        Execute the provided queries and verify the results.
        Optimize performance using the suggested indexes.

### Security and Transactions

The project emphasizes security measures to prevent SQL injection and ensures that all database operations are atomic using transactions. Proper error handling and input validation are implemented throughout the web application.

### Conclusion

This project demonstrates comprehensive database management skills, including schema design, data loading, integrity constraints, complex queries, view creation, web application development, OLAP analysis, and performance optimization through indexing.
