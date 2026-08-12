from fastapi import APIRouter,HTTPException
from schemas import category
from databases import collection4
from bson import ObjectId

categoryrouter=APIRouter()
@categoryrouter.post("/posting_categories", response_model=dict)
def create_category(category_data: category):
    data = category_data.model_dump()
    result = collection4.insert_one(data)
    return {
        "message": "Category created successfully",
        "inserted_id": str(result.inserted_id),
    }


@categoryrouter.get("/get_categories", response_model=list[dict])
def get_all_categories():
    categories = []
    for doc in collection4.find():
        doc["_id"] = str(doc["_id"])
        categories.append(doc)
    return categories


@categoryrouter.get("/getting_single_category{category_id}")
def get_category(category_id: str):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    doc = collection4.find_one({"_id": ObjectId(category_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Category not found")

    doc["_id"] = str(doc["_id"])
    return doc


@categoryrouter.put("/{category_id}")
def update_category(category_id: str, category_data: category):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    update_data = category_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400, detail="No fields provided for update"
        )

    result = collection4.update_one(
        {"_id": ObjectId(category_id)}, {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")

    updated_doc = collection4.find_one({"_id": ObjectId(category_id)})
    updated_doc["_id"] = str(updated_doc["_id"])

    return {
        "message": "Category updated successfully",
        "category": updated_doc,
    }


@categoryrouter.delete("/deleting_categories{category_id}")
def delete_category(category_id: str):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    result = collection4.delete_one({"_id": ObjectId(category_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")

    return {
        "message": "Category deleted successfully",
        "deleted_id": category_id,
    }
