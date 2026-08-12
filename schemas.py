from pydantic import BaseModel,EmailStr,Field

class customer(BaseModel):
    name: str 
    email: EmailStr

class product(BaseModel):
    name: str
    price: float
    category: str
class transaction(BaseModel):
    customer_id: str
    product_id: str
    quantity: int
    total_price: float
class category(BaseModel):
    name: str
    type: str
    products: list[str]

class signup(BaseModel):
    username:str
    email:EmailStr
    password:str =Field(min_length=8,max_length=20)
class login(BaseModel):
    email:EmailStr
    password:str
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
            
