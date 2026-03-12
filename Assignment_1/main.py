from fastapi import FastAPI

app = FastAPI()

# Initial Products
products = [
    {"id": 1, "name": "Notebook", "price": 50, "category": "Stationery", "in_stock": True},
    {"id": 2, "name": "Pen", "price": 10, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Headphones", "price": 1500, "category": "Electronics", "in_stock": True},
    {"id": 4, "name": "Mouse", "price": 500, "category": "Electronics", "in_stock": False},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False},
    ]

@app.get("/")
def home():
    return {"message": "Welcome to FastAPI Store"}

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

#q2
@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):
    result = [p for p in products if p["category"] == category_name]

    if not result:
        return {"error": "No products found in this category"}

    return {
        "category": category_name,
        "products": result,
        "total": len(result)
    }

#3
@app.get("/products/instock")
def get_instock():
    available = [p for p in products if p["in_stock"] == True]

    return {
        "in_stock_products": available,
        "count": len(available)
    }

#q4
@app.get("/store/summary")
def store_summary():
    in_stock_count = len([p for p in products if p["in_stock"]])
    
    out_stock_count = len(products) - in_stock_count
    
    categories = list(set([p["category"] for p in products]))
    
    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": out_stock_count,
        "categories": categories,
    }

#q5
@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    # search products where keyword exists in product name
    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    # if nothing found
    if not results:
        return {"message": "No products matched your search"}

    return {
        "keyword": keyword,
        "results": results,
        "total_matches": len(results)
    }

#q6
@app.get("/products/deals")
def get_deals():

    # find cheapest product
    cheapest = min(products, key=lambda p: p["price"])

    # find most expensive product
    expensive = max(products, key=lambda p: p["price"])
    
    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }
