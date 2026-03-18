from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()

# -----------------------------
# Product Database
# -----------------------------
products = {
    1: {"name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    2: {"name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    3: {"name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    4: {"name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True}
}

cart = []
orders = []
order_id_counter = 1


# -----------------------------
# Models
# -----------------------------
class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# -----------------------------
# Utility Function
# -----------------------------
def calculate_total(product, quantity):
    return product["price"] * quantity


# =============================
# CART SYSTEM
# =============================

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):

    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    product = products[product_id]

    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = calculate_total(product, item["quantity"])
            return {"message": "Cart updated", "cart_item": item}

    subtotal = calculate_total(product, quantity)

    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": subtotal
    }

    cart.append(cart_item)

    return {"message": "Added to cart", "cart_item": cart_item}


@app.get("/cart")
def view_cart():

    if not cart:
        return {"message": "Cart is empty"}

    grand_total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }


@app.delete("/cart/{product_id}")
def remove_item(product_id: int):

    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": "Item removed"}

    raise HTTPException(status_code=404, detail="Item not in cart")


# =============================
# CHECKOUT
# =============================

@app.post("/cart/checkout")
def checkout(data: CheckoutRequest):

    global order_id_counter

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty — add items first")

    placed_orders = []
    grand_total = 0

    for item in cart:
        order = {
            "order_id": order_id_counter,
            "customer_name": data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "total_price": item["subtotal"]
        }

        placed_orders.append(order)
        orders.append(order)

        grand_total += item["subtotal"]
        order_id_counter += 1

    cart.clear()

    return {
        "orders_placed": placed_orders,
        "grand_total": grand_total
    }


# =============================
# ORDERS
# =============================

@app.get("/orders")
def get_orders():
    return {"orders": orders, "total_orders": len(orders)}


# =============================
# Q1 — PRODUCT SEARCH
# =============================

@app.get("/products/search")
def search_products(keyword: str = Query(...)):

    result = [
        {"id": pid, **p}
        for pid, p in products.items()
        if keyword.lower() in p["name"].lower()
    ]

    if not result:
        return {"message": f"No products found for: {keyword}"}

    return {
        "keyword": keyword,
        "total_found": len(result),
        "products": result
    }


# =============================
# Q2 — PRODUCT SORTING
# =============================

@app.get("/products/sort")
def sort_products(
        sort_by: str = Query("price"),
        order: str = Query("asc")
):

    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    reverse = (order == "desc")

    product_list = [{"id": pid, **p} for pid, p in products.items()]

    sorted_products = sorted(
        product_list,
        key=lambda p: p[sort_by],
        reverse=reverse
    )

    return {
        "sort_by": sort_by,
        "order": order,
        "products": sorted_products
    }


# =============================
# Q3 — PAGINATION
# =============================

@app.get("/products/page")
def paginate_products(
        page: int = Query(1, ge=1),
        limit: int = Query(2, ge=1)
):

    product_list = [{"id": pid, **p} for pid, p in products.items()]

    start = (page - 1) * limit
    paged = product_list[start:start + limit]

    return {
        "page": page,
        "limit": limit,
        "total_products": len(product_list),
        "total_pages": -(-len(product_list) // limit),
        "products": paged
    }


# =============================
# Q4 — SEARCH ORDERS
# =============================

@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):

    result = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]

    if not result:
        return {"message": f"No orders found for: {customer_name}"}

    return {
        "customer_name": customer_name,
        "total_found": len(result),
        "orders": result
    }


# =============================
# Q5 — SORT BY CATEGORY
# =============================

@app.get("/products/sort-by-category")
def sort_by_category():

    product_list = [{"id": pid, **p} for pid, p in products.items()]

    result = sorted(
        product_list,
        key=lambda p: (p["category"], p["price"])
    )

    return {
        "products": result,
        "total": len(result)
    }


# =============================
# Q6 — BROWSE (SEARCH + SORT + PAGINATION)
# =============================

@app.get("/products/browse")
def browse_products(
        keyword: str = Query(None),
        sort_by: str = Query("price"),
        order: str = Query("asc"),
        page: int = Query(1, ge=1),
        limit: int = Query(4, ge=1, le=20)
):

    product_list = [{"id": pid, **p} for pid, p in products.items()]

    result = product_list

    # Search
    if keyword:
        result = [
            p for p in result
            if keyword.lower() in p["name"].lower()
        ]

    # Sort
    if sort_by in ["price", "name"]:
        result = sorted(
            result,
            key=lambda p: p[sort_by],
            reverse=(order == "desc")
        )

    # Pagination
    total = len(result)
    start = (page - 1) * limit
    paged = result[start:start + limit]

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": -(-total // limit),
        "products": paged
    }


# =============================
# BONUS — ORDER PAGINATION
# =============================

@app.get("/orders/page")
def get_orders_page(
        page: int = Query(1, ge=1),
        limit: int = Query(3, ge=1, le=20)
):

    start = (page - 1) * limit

    return {
        "page": page,
        "limit": limit,
        "total": len(orders),
        "total_pages": -(-len(orders) // limit),
        "orders": orders[start:start + limit]
    }