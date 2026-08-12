from datetime import datetime
from io import BytesIO
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from schemas import transaction
from databases import collection2
from bson import ObjectId

transactionrouter = APIRouter()


@transactionrouter.post("/posting_transactions", response_model=dict)
def create_transaction(transaction_data: transaction):
    data = transaction_data.model_dump()
    data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = collection2.insert_one(data)
    
    receipt = {
        "receipt_id": f"REC-{str(result.inserted_id)[-6:].upper()}",
        "transaction_id": str(result.inserted_id),
        "issued_at": data["created_at"],
        "status": "COMPLETED",
        "details": data
    }

    return {
        "message": "Transaction created successfully",
        "receipt": receipt
    }


@transactionrouter.get("/getting_transactions", response_model=list[dict])
def get_all_transactions():
    transactions = []
    for doc in collection2.find():
        doc["_id"] = str(doc["_id"])
        transactions.append(doc)
    return transactions


@transactionrouter.get("/{transaction_id}")
def get_transaction(transaction_id: str):
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    doc = collection2.find_one({"_id": ObjectId(transaction_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Transaction not found")

    doc["_id"] = str(doc["_id"])
    return doc


@transactionrouter.get("/receipt/{transaction_id}")
def generate_receipt(transaction_id: str):
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    doc = collection2.find_one({"_id": ObjectId(transaction_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Transaction not found")

    doc["_id"] = str(doc["_id"])
    
    receipt = {
        "title": "PAYMENT RECEIPT",
        "receipt_number": f"REC-{doc['_id'][-6:].upper()}",
        "transaction_id": doc["_id"],
        "date": doc.get("created_at", "N/A"),
        "payment_summary": doc,
        "status": "PAID"
    }
    
    return receipt


@transactionrouter.get("/receipt_pdf/{transaction_id}")
def generate_receipt_pdf(transaction_id: str):
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    doc = collection2.find_one({"_id": ObjectId(transaction_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Transaction not found")

    doc["_id"] = str(doc["_id"])

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(200, 750, "AB INVENTORY MANAGEMENT")
    pdf.setFont("Helvetica", 14)
    pdf.drawString(235, 725, "PAYMENT RECEIPT")
    pdf.line(50, 710, 550, 710)

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 670, f"Receipt No: REC-{doc['_id'][-6:].upper()}")
    pdf.drawString(50, 645, f"Transaction ID: {doc['_id']}")
    pdf.drawString(50, 620, f"Date: {doc.get('created_at', 'N/A')}")
    pdf.drawString(50, 595, f"Customer ID: {doc.get('customer_id', 'N/A')}")
    pdf.drawString(50, 570, f"Product ID: {doc.get('product_id', 'N/A')}")
    pdf.drawString(50, 545, f"Quantity: {doc.get('quantity', 'N/A')}")
    pdf.drawString(50, 520, f"Total Price: ${doc.get('total_price', 0.0)}")
    pdf.drawString(50, 495, "Payment Status: PAID")

    pdf.line(50, 470, 550, 470)
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(200, 450, "Thank you for your business!")

    pdf.save()
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=receipt_{transaction_id}.pdf"}
    )


@transactionrouter.put("/updating_transactions/{transaction_id}")
def update_transaction(transaction_id: str, transaction_data: transaction):
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    update_data = transaction_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400, detail="No fields provided for update"
        )

    result = collection2.update_one(
        {"_id": ObjectId(transaction_id)}, {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")

    updated_doc = collection2.find_one({"_id": ObjectId(transaction_id)})
    updated_doc["_id"] = str(updated_doc["_id"])

    return {
        "message": "Transaction updated successfully",
        "transaction": updated_doc,
    }


@transactionrouter.delete("/deleting_transactions/{transaction_id}")
def delete_transaction(transaction_id: str):
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    result = collection2.delete_one({"_id": ObjectId(transaction_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "message": "Transaction deleted successfully",
        "deleted_id": transaction_id,
    }