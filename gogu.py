import os
from datetime import datetime, timedelta, timezone
from io import BytesIO

import pandas as pd
import streamlit as st
from bson import ObjectId
from jose import JWTError, jwt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Direct module imports
from databases import (
    collection,   # Customers
    collection2,  # Transactions
    collection3,  # Products
    collection4,  # Categories
    collection5,  # Authentication
)
from utils import create_access_token, hash_password, verify_password

st.set_page_config(
    page_title="AB Inventory",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

LOGO = "https://cdn-icons-png.flaticon.com/512/2897/2897785.png"
RESET_SECRET_KEY = os.getenv("secret_key", "YOUR_SUPER_SECRET_RESET_KEY")
ALGORITHM = "HS256"

# -------------------- BACKEND LOGIC & UTILITIES --------------------

def create_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {"sub": email, "exp": expire, "scope": "password_reset"}
    return jwt.encode(payload, RESET_SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str) -> str:
    payload = jwt.decode(token, RESET_SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("scope") != "password_reset":
        raise ValueError("Invalid token scope")
    email = payload.get("sub")
    if not email:
        raise ValueError("Invalid token payload")
    return email

def get_all_products():
    products = []
    for doc in collection3.find():
        doc["_id"] = str(doc["_id"])
        products.append(doc)
    return products

def get_all_categories():
    categories = []
    for doc in collection4.find():
        doc["_id"] = str(doc["_id"])
        categories.append(doc)
    return categories

def get_all_customers():
    customers = []
    for doc in collection.find():
        doc["_id"] = str(doc["_id"])
        customers.append(doc)
    return customers

def get_all_transactions():
    transactions = []
    for doc in collection2.find():
        doc["_id"] = str(doc["_id"])
        transactions.append(doc)
    return transactions

def generate_receipt_pdf_bytes(transaction_id: str):
    if not ObjectId.is_valid(transaction_id):
        return None
    doc = collection2.find_one({"_id": ObjectId(transaction_id)})
    if not doc:
        return None

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
    return buffer.getvalue()

# -------------------- SESSION --------------------

if "token" not in st.session_state:
    st.session_state.token = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# -------------------- STYLE --------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

*{font-family:'Plus Jakarta Sans',sans-serif}
.stApp{
    background:
    radial-gradient(circle at 20% 0%,#1e1b4b 0,transparent 35%),
    radial-gradient(circle at 100% 0%,#0c4a6e 0,transparent 28%),
    #080c15;
    color:#f8fafc;
}
section[data-testid="stSidebar"]{
    background:#0b1120!important;
    border-right:1px solid #1e293b;
}
header[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}

h1,h2,h3{color:#f8fafc!important}

.header{
    display:flex;
    align-items:center;
    gap:12px;
    margin-bottom:3px;
}
.header img{width:40px;height:40px}
.header h1{font-size:1.8rem;margin:0;font-weight:800}
.subtitle{color:#94a3b8;margin:0 0 20px}

.card{
    background:rgba(20,28,45,.78);
    border:1px solid rgba(255,255,255,.07);
    border-radius:16px;
    padding:18px;
    margin-bottom:14px;
}
.kpi{
    background:linear-gradient(145deg,#182235,#101827);
    border:1px solid #263249;
    border-radius:14px;
    padding:16px;
}
.kpi-icon{font-size:1.25rem}
.kpi-label{
    color:#94a3b8;
    font-size:.72rem;
    text-transform:uppercase;
    font-weight:700;
    letter-spacing:.7px;
}
.kpi-value{
    font-size:1.8rem;
    font-weight:800;
    margin-top:4px;
}
.stButton>button{
    width:100%;
    border:0;
    border-radius:9px;
    background:linear-gradient(135deg,#6366f1,#4f46e5);
    color:white!important;
    font-weight:700;
}
.stDownloadButton>button{
    width:100%;
    border:0;
    border-radius:9px;
    background:#059669;
    color:white!important;
    font-weight:700;
}
.stTextInput input,
.stNumberInput input,
.stTextArea textarea{
    background:#0f172a!important;
    color:white!important;
    border:1px solid #263249!important;
    border-radius:9px!important;
}
.stTabs [data-baseweb="tab-list"]{
    background:#0f172a;
    padding:5px;
    border-radius:10px;
    gap:5px;
}
.stTabs [aria-selected="true"]{
    background:#6366f1!important;
    color:white!important;
    border-radius:8px;
}
</style>
""", unsafe_allow_html=True)

def header(icon, title, subtitle):
    st.markdown(
        f'<div class="header"><img src="{icon}"><h1>{title}</h1></div>'
        f'<p class="subtitle">{subtitle}</p>',
        unsafe_allow_html=True
    )

def kpi(icon, title, value):
    st.markdown(
        f'<div class="kpi"><div class="kpi-icon">{icon}</div>'
        f'<div class="kpi-label">{title}</div>'
        f'<div class="kpi-value">{value}</div></div>',
        unsafe_allow_html=True
    )

# -------------------- LOGIN --------------------

if not st.session_state.logged_in:

    _, col, _ = st.columns([1, 1.4, 1])

    with col:
        st.markdown(
            f"""
            <div style="text-align:center;padding:45px 0 20px">
                <img src="{LOGO}" width="70">
                <h1 style="margin:8px 0 2px">AB Inventory</h1>
                <p style="color:#64748b">
                    Simple, smart inventory management
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="card">', unsafe_allow_html=True)

        mode = st.radio(
            "Account",
            ["Log In", "Create Account", "Forgot Password"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if mode == "Log In":

            with st.form("login"):
                email = st.text_input("Email", placeholder="name@company.com")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("🔐 Sign In")

                if submit:
                    if not email or not password:
                        st.warning("Enter your email and password.")
                    else:
                        user = collection5.find_one({"email": email})
                        if user and verify_password(password, user["password"]):
                            token = create_access_token({
                                "email": user["email"],
                                "username": user["username"],
                                "user_id": str(user["_id"])
                            })
                            st.session_state.token = token
                            st.session_state.logged_in = True
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")

        elif mode == "Create Account":

            with st.form("register"):
                username = st.text_input("Username", placeholder="johndoe")
                email = st.text_input("Email", placeholder="name@company.com")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("✨ Create Account")

                if submit:
                    if not username or not email or not password:
                        st.warning("Complete all fields.")
                    else:
                        if collection5.find_one({"email": email}):
                            st.error("User already exists.")
                        else:
                            hashed_pwd = hash_password(password)
                            res = collection5.insert_one({
                                "username": username,
                                "email": email,
                                "password": hashed_pwd
                            })
                            token = create_access_token({
                                "email": email,
                                "username": username,
                                "user_id": str(res.inserted_id)
                            })
                            st.session_state.token = token
                            st.session_state.logged_in = True
                            st.rerun()

        elif mode == "Forgot Password":

            step1, step2 = st.tabs(["1. Get Token", "2. Reset Password"])

            with step1:
                with st.form("request_reset"):
                    email = st.text_input("Email", placeholder="name@company.com")
                    submit = st.form_submit_button("📩 Request Reset Code")

                    if submit:
                        if not email:
                            st.warning("Enter your registered email.")
                        else:
                            user = collection5.find_one({"email": email})
                            if not user:
                                st.info("If an account exists with this email, a reset token has been issued.")
                            else:
                                reset_token = create_reset_token(email)
                                st.success("Reset token generated successfully!")
                                st.code(reset_token, language="text")
                                st.info("Copy this token and go to the '2. Reset Password' tab.")

            with step2:
                with st.form("reset_password"):
                    token = st.text_input("Reset Token", placeholder="Paste reset token here")
                    new_password = st.text_input("New Password", type="password")
                    submit = st.form_submit_button("🔑 Reset Password")

                    if submit:
                        if not token or not new_password:
                            st.warning("Please provide both the token and new password.")
                        else:
                            try:
                                email_from_tok = verify_reset_token(token)
                                user = collection5.find_one({"email": email_from_tok})
                                if not user:
                                    st.error("User not found.")
                                else:
                                    new_hashed = hash_password(new_password)
                                    collection5.update_one({"email": email_from_tok}, {"$set": {"password": new_hashed}})
                                    st.success("Password updated successfully! You can now log in.")
                            except Exception:
                                st.error("Invalid or expired reset token.")

        st.markdown('</div>', unsafe_allow_html=True)

# -------------------- APPLICATION --------------------

else:

    # Direct database queries
    products = get_all_products()
    categories = get_all_categories()
    customers = get_all_customers()
    transactions = get_all_transactions()

    products_df = pd.DataFrame(products)
    categories_df = pd.DataFrame(categories)
    customers_df = pd.DataFrame(customers)
    transactions_df = pd.DataFrame(transactions)

    # Sidebar
    with st.sidebar:

        st.markdown(
            f"""
            <div style="text-align:center;padding:10px 0">
                <img src="{LOGO}" width="52">
                <h3 style="margin:6px 0">AB Inventory</h3>
                <small style="color:#64748b">Management Suite</small>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        pages = {
            "🏠 Dashboard":"Dashboard",
            "📦 Products":"Products",
            "🏷️ Categories":"Categories",
            "👤 Customers":"Customers",
            "💳 Transactions":"Transactions"
        }

        selected = st.radio(
            "Navigation",
            pages.keys(),
            label_visibility="collapsed"
        )

        st.session_state.page = pages[selected]

        st.divider()

        if st.button("🚪 Log Out"):
            st.session_state.token = None
            st.session_state.logged_in = False
            st.rerun()

    # -------------------- DASHBOARD --------------------

    if st.session_state.page == "Dashboard":

        header(LOGO, "Dashboard", "Everything you need at a glance.")

        c1, c2, c3, c4 = st.columns(4)

        with c1: kpi("📦", "Products", len(products))
        with c2: kpi("🏷️", "Categories", len(categories))
        with c3: kpi("👥", "Customers", len(customers))
        with c4: kpi("💳", "Sales", len(transactions))

        st.write("")

        left, right = st.columns([1.6, 1])

        with left:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📈 Sales Activity")

            if not transactions_df.empty:
                price_col = next(
                    (x for x in ["total_price", "total_amount", "amount", "price"] if x in transactions_df.columns),
                    None
                )

                if price_col:
                    chart = transactions_df[[price_col]].copy()
                    chart[price_col] = pd.to_numeric(chart[price_col], errors="coerce")
                    st.line_chart(chart)
                else:
                    st.dataframe(transactions_df.tail(8), use_container_width=True, hide_index=True)
            else:
                st.info("No sales recorded yet.")

            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("⚡ Quick Actions")

            if st.button("➕ Add Product"):
                st.session_state.page = "Products"
                st.rerun()

            if st.button("👤 Add Customer"):
                st.session_state.page = "Customers"
                st.rerun()

            if st.button("💳 Record Sale"):
                st.session_state.page = "Transactions"
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🧾 Recent Transactions")

        if not transactions_df.empty:
            st.dataframe(transactions_df.tail(10), use_container_width=True, hide_index=True)
        else:
            st.info("No transactions available.")

        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------- PRODUCTS --------------------

    elif st.session_state.page == "Products":

        header(LOGO, "Products", "Manage your product catalog.")

        browse, add, edit, delete = st.tabs(["📋 Browse", "➕ Add", "✏️ Edit", "🗑️ Delete"])

        with browse:
            search = st.text_input("🔎 Search", placeholder="Search products...")
            df = products_df.copy()

            if search and not df.empty:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]

            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No products found.")

        with add:
            with st.form("add_product"):
                c1, c2 = st.columns(2)
                with c1: name = st.text_input("Product Name")
                with c2: category = st.text_input("Category")
                price = st.number_input("Price", min_value=0.0, step=0.5, format="%.2f")

                if st.form_submit_button("➕ Add Product"):
                    collection3.insert_one({
                        "name": name,
                        "price": float(price),
                        "category": category
                    })
                    st.success("Product added!")
                    st.rerun()

        with edit:
            with st.form("edit_product"):
                product_id = st.text_input("Product ID")
                name = st.text_input("New Name")
                price = st.number_input("New Price", min_value=0.0, format="%.2f")
                category = st.text_input("New Category")

                if st.form_submit_button("💾 Save Changes"):
                    if not ObjectId.is_valid(product_id):
                        st.error("Invalid Product ID format.")
                    else:
                        res = collection3.update_one(
                            {"_id": ObjectId(product_id)},
                            {"$set": {"name": name, "price": float(price), "category": category}}
                        )
                        if res.matched_count > 0:
                            st.success("Product updated!")
                            st.rerun()
                        else:
                            st.error("Product not found.")

        with delete:
            with st.form("delete_product"):
                product_id = st.text_input("Product ID")
                confirm = st.checkbox("I understand this cannot be undone.")

                if st.form_submit_button("🗑️ Delete Product"):
                    if not confirm:
                        st.warning("Confirm the deletion first.")
                    elif not ObjectId.is_valid(product_id):
                        st.error("Invalid Product ID format.")
                    else:
                        res = collection3.delete_one({"_id": ObjectId(product_id)})
                        if res.deleted_count > 0:
                            st.success("Product deleted.")
                            st.rerun()
                        else:
                            st.error("Product not found.")

    # -------------------- CATEGORIES --------------------

    elif st.session_state.page == "Categories":

        header(LOGO, "Categories", "Organize your products.")

        browse, add = st.tabs(["📋 Browse", "➕ Add"])

        with browse:
            if categories_df.empty:
                st.info("No categories found.")
            else:
                st.dataframe(categories_df, use_container_width=True, hide_index=True)

        with add:
            with st.form("add_category"):
                name = st.text_input("Category Name")
                category_type = st.text_input("Category Type")
                products_text = st.text_area("Products", placeholder="Mouse, Keyboard, Monitor")

                if st.form_submit_button("➕ Create Category"):
                    product_list = [x.strip() for x in products_text.split(",") if x.strip()]
                    collection4.insert_one({
                        "name": name,
                        "type": category_type,
                        "products": product_list
                    })
                    st.success("Category created!")
                    st.rerun()

    # -------------------- CUSTOMERS --------------------

    elif st.session_state.page == "Customers":

        header(LOGO, "Customers", "Manage your customer directory.")

        browse, add = st.tabs(["👥 Directory", "➕ Add Customer"])

        with browse:
            search = st.text_input("🔎 Search customers", placeholder="Name or email...")
            df = customers_df.copy()

            if search and not df.empty:
                df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]

            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No customers found.")

        with add:
            with st.form("add_customer"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")

                if st.form_submit_button("➕ Add Customer"):
                    collection.insert_one({
                        "name": name,
                        "email": email
                    })
                    st.success("Customer added!")
                    st.rerun()

    # -------------------- TRANSACTIONS --------------------

    elif st.session_state.page == "Transactions":

        header(LOGO, "Transactions", "Record sales and generate receipts.")

        ledger, sale, receipt = st.tabs(["📋 Ledger", "➕ New Sale", "🧾 Receipt"])

        with ledger:
            if transactions_df.empty:
                st.info("No transactions found.")
            else:
                st.dataframe(transactions_df, use_container_width=True, hide_index=True)

        with sale:
            with st.form("new_sale"):
                c1, c2 = st.columns(2)
                with c1:
                    customer_id = st.text_input("Customer ID")
                    product_id = st.text_input("Product ID")
                with c2:
                    quantity = st.number_input("Quantity", min_value=1, step=1)
                    total = st.number_input("Total Amount", min_value=0.0, format="%.2f")

                if st.form_submit_button("💳 Record Sale"):
                    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    collection2.insert_one({
                        "customer_id": customer_id,
                        "product_id": product_id,
                        "quantity": int(quantity),
                        "total_price": float(total),
                        "created_at": created_at
                    })
                    st.success("Sale recorded!")
                    st.rerun()

        with receipt:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🧾 Generate Receipt")

            tx_id = st.text_input("Transaction ID", placeholder="Enter transaction ID")

            if st.button("📄 Generate PDF"):
                if not tx_id:
                    st.warning("Enter a transaction ID.")
                else:
                    pdf_bytes = generate_receipt_pdf_bytes(tx_id)
                    if pdf_bytes:
                        st.success("Receipt ready!")
                        st.download_button(
                            "📥 Download Receipt",
                            pdf_bytes,
                            file_name=f"receipt_{tx_id}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("Could not generate receipt or transaction not found.")

            st.markdown('</div>', unsafe_allow_html=True)