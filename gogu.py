import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="AB Inventory",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = "http://127.0.0.1:8000"
LOGO = "https://cdn-icons-png.flaticon.com/512/2897/2897785.png"

# -------------------- SESSION --------------------

if "session" not in st.session_state:
    st.session_state.session = requests.Session()

if "token" not in st.session_state:
    st.session_state.token = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

def headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

def request(method, url, **kwargs):
    try:
        return getattr(st.session_state.session, method)(
            API + url, headers=headers(), timeout=10, **kwargs
        )
    except requests.RequestException:
        return None

def data(res):
    if not res:
        return []
    try:
        return res.json()
    except:
        return []

def error(res, default="Something went wrong."):
    try:
        return res.json().get("detail", default)
    except:
        return default

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
                        res = request(
                            "post",
                            "/authent/login",
                            json={"email":email,"password":password}
                        )

                        if res and res.status_code == 200:
                            st.session_state.token = data(res).get("token")
                            st.session_state.logged_in = True
                            st.rerun()
                        else:
                            st.error(error(res,"Invalid email or password."))

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
                        res = request(
                            "post",
                            "/authent/register",
                            json={
                                "username":username,
                                "email":email,
                                "password":password
                            }
                        )

                        if res and res.status_code == 200:
                            st.session_state.token = data(res).get("token")
                            st.session_state.logged_in = True
                            st.rerun()
                        else:
                            st.error(error(res,"Could not create account."))

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
                            res = request(
                                "post",
                                "/authent/forgot-password",
                                json={"email": email}
                            )

                            if res and res.status_code == 200:
                                res_data = data(res)
                                st.success(res_data.get("message", "Request submitted."))
                                if "reset_token" in res_data:
                                    st.code(res_data["reset_token"], language="text")
                                    st.info("Copy this token and go to the '2. Reset Password' tab.")
                            else:
                                st.error(error(res, "Request failed."))

            with step2:
                with st.form("reset_password"):
                    token = st.text_input("Reset Token", placeholder="Paste reset token here")
                    new_password = st.text_input("New Password", type="password")
                    submit = st.form_submit_button("🔑 Reset Password")

                    if submit:
                        if not token or not new_password:
                            st.warning("Please provide both the token and new password.")
                        else:
                            res = request(
                                "post",
                                "/authent/reset-password",
                                json={"token": token, "new_password": new_password}
                            )

                            if res and res.status_code == 200:
                                st.success("Password updated successfully! You can now log in.")
                            else:
                                st.error(error(res, "Invalid or expired token."))

        st.markdown('</div>', unsafe_allow_html=True)

# -------------------- APPLICATION --------------------

else:

    # Load data
    products = data(request("get","/products/products-get/"))
    categories = data(request("get","/categories/get_categories"))
    customers = data(request("get","/customers/getting_customer"))
    transactions = data(request("get","/transactions/getting_transactions"))

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

        header(
            LOGO,
            "Dashboard",
            "Everything you need at a glance."
        )

        c1,c2,c3,c4 = st.columns(4)

        with c1: kpi("📦","Products",len(products))
        with c2: kpi("🏷️","Categories",len(categories))
        with c3: kpi("👥","Customers",len(customers))
        with c4: kpi("💳","Sales",len(transactions))

        st.write("")

        left,right = st.columns([1.6,1])

        with left:
            st.markdown('<div class="card">',unsafe_allow_html=True)
            st.subheader("📈 Sales Activity")

            if not transactions_df.empty:
                price_col = next(
                    (x for x in
                     ["total_price","total_amount","amount","price"]
                     if x in transactions_df.columns),
                    None
                )

                if price_col:
                    chart = transactions_df[[price_col]].copy()
                    chart[price_col] = pd.to_numeric(
                        chart[price_col],
                        errors="coerce"
                    )
                    st.line_chart(chart)
                else:
                    st.dataframe(
                        transactions_df.tail(8),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info("No sales recorded yet.")

            st.markdown('</div>',unsafe_allow_html=True)

        with right:
            st.markdown('<div class="card">',unsafe_allow_html=True)
            st.subheader("⚡ Quick Actions")

            if st.button("➕ Add Product"):
                st.session_state.page="Products"
                st.rerun()

            if st.button("👤 Add Customer"):
                st.session_state.page="Customers"
                st.rerun()

            if st.button("💳 Record Sale"):
                st.session_state.page="Transactions"
                st.rerun()

            st.markdown('</div>',unsafe_allow_html=True)

        st.markdown('<div class="card">',unsafe_allow_html=True)
        st.subheader("🧾 Recent Transactions")

        if not transactions_df.empty:
            st.dataframe(
                transactions_df.tail(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No transactions available.")

        st.markdown('</div>',unsafe_allow_html=True)

    # -------------------- PRODUCTS --------------------

    elif st.session_state.page == "Products":

        header(
            LOGO,
            "Products",
            "Manage your product catalog."
        )

        browse,add,edit,delete = st.tabs(
            ["📋 Browse","➕ Add","✏️ Edit","🗑️ Delete"]
        )

        with browse:

            search = st.text_input(
                "🔎 Search",
                placeholder="Search products..."
            )

            df = products_df.copy()

            if search and not df.empty:
                df = df[
                    df.astype(str)
                    .apply(
                        lambda x:x.str.contains(
                            search,
                            case=False,
                            na=False
                        )
                    )
                    .any(axis=1)
                ]

            if not df.empty:
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No products found.")

        with add:

            with st.form("add_product"):

                c1,c2 = st.columns(2)

                with c1:
                    name = st.text_input("Product Name")

                with c2:
                    category = st.text_input("Category")

                price = st.number_input(
                    "Price",
                    min_value=0.0,
                    step=0.5,
                    format="%.2f"
                )

                if st.form_submit_button("➕ Add Product"):

                    res = request(
                        "post",
                        "/products/products_post/",
                        json={
                            "name":name,
                            "price":price,
                            "category":category
                        }
                    )

                    if res and res.status_code == 200:
                        st.success("Product added!")
                        st.rerun()
                    else:
                        st.error(error(res))

        with edit:

            with st.form("edit_product"):

                product_id = st.text_input("Product ID")
                name = st.text_input("New Name")
                price = st.number_input(
                    "New Price",
                    min_value=0.0,
                    format="%.2f"
                )
                category = st.text_input("New Category")

                if st.form_submit_button("💾 Save Changes"):

                    res = request(
                        "put",
                        f"/products/{product_id}",
                        json={
                            "name":name,
                            "price":price,
                            "category":category
                        }
                    )

                    if res and res.status_code == 200:
                        st.success("Product updated!")
                        st.rerun()
                    else:
                        st.error(error(res))

        with delete:

            with st.form("delete_product"):

                product_id = st.text_input("Product ID")
                confirm = st.checkbox("I understand this cannot be undone.")

                if st.form_submit_button("🗑️ Delete Product"):

                    if not confirm:
                        st.warning("Confirm the deletion first.")
                    else:

                        res = request(
                            "delete",
                            f"/products/{product_id}"
                        )

                        if res and res.status_code == 200:
                            st.success("Product deleted.")
                            st.rerun()
                        else:
                            st.error(error(res))

    # -------------------- CATEGORIES --------------------

    elif st.session_state.page == "Categories":

        header(
            LOGO,
            "Categories",
            "Organize your products."
        )

        browse,add = st.tabs(
            ["📋 Browse","➕ Add"]
        )

        with browse:

            if categories_df.empty:
                st.info("No categories found.")
            else:
                st.dataframe(
                    categories_df,
                    use_container_width=True,
                    hide_index=True
                )

        with add:

            with st.form("add_category"):

                name = st.text_input("Category Name")
                category_type = st.text_input("Category Type")
                products_text = st.text_area(
                    "Products",
                    placeholder="Mouse, Keyboard, Monitor"
                )

                if st.form_submit_button("➕ Create Category"):

                    product_list = [
                        x.strip()
                        for x in products_text.split(",")
                        if x.strip()
                    ]

                    res = request(
                        "post",
                        "/categories/posting_categories",
                        json={
                            "name":name,
                            "type":category_type,
                            "products":product_list
                        }
                    )

                    if res and res.status_code == 200:
                        st.success("Category created!")
                        st.rerun()
                    else:
                        st.error(error(res))

    # -------------------- CUSTOMERS --------------------

    elif st.session_state.page == "Customers":

        header(
            LOGO,
            "Customers",
            "Manage your customer directory."
        )

        browse,add = st.tabs(
            ["👥 Directory","➕ Add Customer"]
        )

        with browse:

            search = st.text_input(
                "🔎 Search customers",
                placeholder="Name or email..."
            )

            df = customers_df.copy()

            if search and not df.empty:
                df = df[
                    df.astype(str)
                    .apply(
                        lambda x:x.str.contains(
                            search,
                            case=False,
                            na=False
                        )
                    )
                    .any(axis=1)
                ]

            if not df.empty:
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No customers found.")

        with add:

            with st.form("add_customer"):

                name = st.text_input("Full Name")
                email = st.text_input("Email")

                if st.form_submit_button("➕ Add Customer"):

                    res = request(
                        "post",
                        "/customers/posting_customer",
                        json={
                            "name":name,
                            "email":email
                        }
                    )

                    if res and res.status_code == 200:
                        st.success("Customer added!")
                        st.rerun()
                    else:
                        st.error(error(res))

    # -------------------- TRANSACTIONS --------------------

    elif st.session_state.page == "Transactions":

        header(
            LOGO,
            "Transactions",
            "Record sales and generate receipts."
        )

        ledger,sale,receipt = st.tabs(
            ["📋 Ledger","➕ New Sale","🧾 Receipt"]
        )

        with ledger:

            if transactions_df.empty:
                st.info("No transactions found.")
            else:
                st.dataframe(
                    transactions_df,
                    use_container_width=True,
                    hide_index=True
                )

        with sale:

            with st.form("new_sale"):

                c1,c2 = st.columns(2)

                with c1:
                    customer_id = st.text_input("Customer ID")
                    product_id = st.text_input("Product ID")

                with c2:
                    quantity = st.number_input(
                        "Quantity",
                        min_value=1,
                        step=1
                    )
                    total = st.number_input(
                        "Total Amount",
                        min_value=0.0,
                        format="%.2f"
                    )

                if st.form_submit_button("💳 Record Sale"):

                    res = request(
                        "post",
                        "/transactions/posting_transactions",
                        json={
                            "customer_id":customer_id,
                            "product_id":product_id,
                            "quantity":quantity,
                            "total_price":total
                        }
                    )

                    if res and res.status_code == 200:
                        st.success("Sale recorded!")
                        st.rerun()
                    else:
                        st.error(error(res))

        with receipt:

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True
            )

            st.subheader("🧾 Generate Receipt")

            tx_id = st.text_input(
                "Transaction ID",
                placeholder="Enter transaction ID"
            )

            if st.button("📄 Generate PDF"):

                if not tx_id:
                    st.warning("Enter a transaction ID.")
                else:

                    res = request(
                        "get",
                        f"/transactions/receipt_pdf/{tx_id}"
                    )

                    if res and res.status_code == 200:

                        st.success("Receipt ready!")

                        st.download_button(
                            "📥 Download Receipt",
                            res.content,
                            file_name=f"receipt_{tx_id}.pdf",
                            mime="application/pdf"
                        )

                    else:
                        st.error(
                            "Could not generate the receipt."
                        )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )