from fastapi import APIRouter,HTTPException
from schemas import customer
from databases import collection
from bson import ObjectId

customerouter=APIRouter()

@customerouter.post("/posting_customer", response_model=dict)
def create_customer(customer_data: customer):
    data = customer_data.model_dump()
    result = collection.insert_one(data)
    return {
        "message": "Customer created successfully",
        "inserted_id": str(result.inserted_id),
    }


@customerouter.get("/getting_customer", response_model=list[dict])
def get_all_customers():
    customers = []
    for doc in collection.find():
        doc["_id"] = str(doc["_id"])
        customers.append(doc)
    return customers


@customerouter.get("/getting_single_customer{customer_id}")
def get_customer(customer_id: str):
    if not ObjectId.is_valid(customer_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    doc = collection.find_one({"_id": ObjectId(customer_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Customer not found")

    doc["_id"] = str(doc["_id"])
    return doc


@customerouter.put("/updating_customer{customer_id}")
def update_customer(customer_id: str, customer_data: customer):
    if not ObjectId.is_valid(customer_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    update_data = customer_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400, detail="No fields provided for update"
        )

    result = collection.update_one(
        {"_id": ObjectId(customer_id)}, {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")

    updated_doc = collection.find_one({"_id": ObjectId(customer_id)})
    updated_doc["_id"] = str(updated_doc["_id"])

    return {
        "message": "Customer updated successfully",
        "customer": updated_doc,
    }


@customerouter.delete("/deleting_customer{customer_id}")
def delete_customer(customer_id: str):
    if not ObjectId.is_valid(customer_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    result = collection.delete_one({"_id": ObjectId(customer_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {
        "message": "Customer deleted successfully",
        "deleted_id": customer_id,
    }