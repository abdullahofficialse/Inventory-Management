from fastapi import APIRouter, HTTPException
from databases import collection3
from schemas import product
from bson import ObjectId


productrouter = APIRouter()

@productrouter.post("/products_post/", response_model=dict)
def create_product(product: product):
    product_dict = product.model_dump()
    result = collection3.insert_one(product_dict)

    return {
        "message": "Product created successfully",
        "inserted_id": str(result.inserted_id),
    }

@productrouter.get("/products-get/", response_model=list[dict])
def get_all_products():
    products = []
    for doc in collection3.find():
        doc["_id"] = str(doc["_id"])
        products.append(doc)
    return products

@productrouter.get("/product_get/{product_id}")
def get_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    doc = collection3.find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    doc["_id"] = str(doc["_id"])
    return doc

@productrouter.put("/{product_id}")
def update_product(product_id: str, product: product):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    update_data = product.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400, detail="No fields provided for update"
        )
    result = collection3.update_one(
        {"_id": ObjectId(product_id)}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    updated_doc = collection3.find_one({"_id": ObjectId(product_id)})
    updated_doc["_id"] = str(updated_doc["_id"])
    return {
        "message": "Product updated successfully",
        "product": updated_doc,
    }    

@productrouter.delete("/{product_id}")
def delete_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    result = collection3.delete_one({"_id": ObjectId(product_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "message": "Product deleted successfully",
        "deleted_id": product_id,
    }

@productrouter.get("/products/count/{product_name}")
def get_product_count(product_name: str):
    count = collection3.count_documents({"name": product_name})
    return {
        "product_name": product_name,
        "count": count
    }

@productrouter.get("/products/count-all/")
def get_all_products_count():
    pipeline = [
        {"$group": {"_id": "$name", "count": {"$sum": 1}}},
        {"$project": {"product_name": "$_id", "count": 1, "_id": 0}}
    ]
    return list(collection3.aggregate(pipeline))