from fastapi import FastAPI
from routers import products, transactions, categories, customers,auth

app = FastAPI()
@app.get("/")
def get():
    return {"Welcome to Inventory Management API"}

app.include_router(auth.router,prefix="/authent",tags=["authentication"])
app.include_router(products.productrouter, prefix="/products", tags=["Products"])   
app.include_router(transactions.transactionrouter, prefix="/transactions", tags=["Transactions"])
app.include_router(categories.categoryrouter, prefix="/categories", tags=["Categories"])
app.include_router(customers.customerouter, prefix="/customers", tags=["Customers"])
