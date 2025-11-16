from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
import jwt
from datetime import datetime, timedelta
import secrets
from passlib.context import CryptContext
import json
import os
import random
import uuid

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["md5_crypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-for-development"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

SECRET_KEY = os.getenv("SECRET_KEY", "5L5vfBJhjFPBGfMtXh_m5AjPVBXNTXCcPyqlYyJTsOU")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "70"))

# Get allowed origins from environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:3000",
    "https://pesaprime.vercel.app"  # Your Vercel domain
]

# File-based storage
USERS_FILE = "users.json"
USER_ACTIVITY_FILE = "user_activity.json"

app = FastAPI(
    title="Pesdaprime API",
    description="Personal Finance Dashboard Backend",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use absolute paths for production
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
USER_ACTIVITY_FILE = os.path.join(BASE_DIR, "user_activity.json")

# Pydantic models
class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone_number: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone_number: str
    created_at: str

class AuthResponse(BaseModel):
    success: bool
    message: str
    access_token: str
    token_type: str
    user: UserResponse

class WalletData(BaseModel):
    balance: float
    equity: float
    currency: str

class DepositRequest(BaseModel):
    amount: float
    phone_number: str

class WithdrawRequest(BaseModel):
    amount: float
    phone_number: str

class InvestmentRequest(BaseModel):
    asset_id: str
    amount: float
    phone_number: str

class TransactionResponse(BaseModel):
    success: bool
    message: str
    new_balance: float
    new_equity: float
    transaction_id: str

class Asset(BaseModel):
    id: str
    name: str
    symbol: str
    type: str
    current_price: float
    change_percentage: float
    moving_average: float
    trend: str
    chart_url: str

class UserInvestment(BaseModel):
    id: str
    user_phone: str
    asset_id: str
    asset_name: str
    invested_amount: float
    current_value: float
    units: float
    entry_price: float
    current_price: float
    profit_loss: float
    profit_loss_percentage: float
    status: str
    created_at: str

class UserActivity(BaseModel):
    id: str
    user_phone: str
    activity_type: str
    amount: float
    description: str
    timestamp: str
    status: str

# Storage functions
@app.on_event("startup")
async def startup_event():
    """Ensure required files exist on startup"""
    for file_path in [USERS_FILE, USER_ACTIVITY_FILE]:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)
            print(f"Created {file_path}")

# Update your file paths in storage functions
def load_data(filename, default={}):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return default
    return default

def save_data(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
        

def get_next_id(data):
    """Generate next ID for data that uses numeric IDs"""
    if not data:
        return "1"
    
    numeric_keys = []
    for key in data.keys():
        try:
            numeric_keys.append(int(key))
        except ValueError:
            continue
    
    if not numeric_keys:
        return "1"
    
    max_id = max(numeric_keys)
    return str(max_id + 1)

def generate_user_id():
    """Generate a unique user ID"""
    return str(uuid.uuid4())

# Load initial data
users_db = load_data(USERS_FILE)
user_activities_db = load_data(USER_ACTIVITY_FILE, default={})
user_investments_db = load_data("user_investments.json", default={})
user_wallets_db = load_data("user_wallets.json", default={})

# Initialize wallet for existing users
for user_email, user_data in users_db.items():
    if isinstance(user_data, dict) and "phone_number" in user_data:
        phone_number = user_data["phone_number"]
        if phone_number not in user_wallets_db:
            user_wallets_db[phone_number] = {
                "balance": 0.0,
                "equity": 0.0,
                "currency": "KES"
            }

# Mock market data
mock_assets = [
    {
        "id": "1", "name": "EUR/USD", "symbol": "EURUSD", "type": "forex",
        "base_price": 1.0850, "volatility": 0.002, "chart_url": "https://www.tradingview.com/chart/?symbol=FX:EURUSD"
    },
    {
        "id": "2", "name": "Apple Inc", "symbol": "AAPL", "type": "stock", 
        "base_price": 185.50, "volatility": 0.015, "chart_url": "https://www.tradingview.com/chart/?symbol=NASDAQ:AAPL"
    },
    {
        "id": "3", "name": "Bitcoin", "symbol": "BTCUSD", "type": "crypto",
        "base_price": 43250.00, "volatility": 0.025, "chart_url": "https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT"
    },
    {
        "id": "4", "name": "Gold", "symbol": "XAUUSD", "type": "commodity",
        "base_price": 2035.00, "volatility": 0.008, "chart_url": "https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD"
    },
    {
        "id": "5", "name": "Tesla Inc", "symbol": "TSLA", "type": "stock",
        "base_price": 245.75, "volatility": 0.020, "chart_url": "https://www.tradingview.com/chart/?symbol=NASDAQ:TSLA"
    }
]

def generate_dynamic_prices():
    """Generate realistic dynamic prices based on volatility"""
    assets_with_prices = []
    for asset in mock_assets:
        change = random.uniform(-asset["volatility"], asset["volatility"])
        current_price = asset["base_price"] * (1 + change)
        change_percentage = change * 100
        
        moving_average = asset["base_price"] * (1 + random.uniform(-0.005, 0.005))
        
        assets_with_prices.append({
            **asset,
            "current_price": round(current_price, 4),
            "change_percentage": round(change_percentage, 2),
            "moving_average": round(moving_average, 4),
            "trend": "up" if change_percentage >= 0 else "down"
        })
    
    return assets_with_prices

class PnLData(BaseModel):
    profit_loss: float
    percentage: float
    trend: str
    
    
# Utility functions
def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        return plain_password == hashed_password

def get_password_hash(password):
    try:
        return pwd_context.hash(password)
    except:
        return password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    users = load_data(USERS_FILE)
    user = users.get(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def log_user_activity(user_phone: str, activity_type: str, amount: float, description: str, status: str = "completed"):
    """Log user activity for tracking"""
    activities = load_data(USER_ACTIVITY_FILE, default={})
    activity_id = get_next_id(activities)
    
    activity = {
        "id": activity_id,
        "user_phone": user_phone,
        "activity_type": activity_type,
        "amount": amount,
        "description": description,
        "timestamp": datetime.utcnow().isoformat(),
        "status": status
    }
    
    activities[activity_id] = activity
    save_data(activities, USER_ACTIVITY_FILE)
    return activity

def update_investment_values(user_phone: str):
    """Update investment values based on current market prices"""
    investments = load_data("user_investments.json", default={})
    current_assets = generate_dynamic_prices()
    
    for inv_id, investment in investments.items():
        if investment["user_phone"] == user_phone and investment["status"] == "active":
            asset = next((a for a in current_assets if a["id"] == investment["asset_id"]), None)
            if asset:
                current_value = investment["units"] * asset["current_price"]
                profit_loss = current_value - investment["invested_amount"]
                profit_loss_percentage = (profit_loss / investment["invested_amount"]) * 100
                
                investment.update({
                    "current_value": current_value,
                    "current_price": asset["current_price"],
                    "profit_loss": profit_loss,
                    "profit_loss_percentage": profit_loss_percentage
                })
    
    save_data(investments, "user_investments.json")

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to PesaDash API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "PesaDash API", "timestamp": datetime.utcnow().isoformat()}

# Authentication endpoints
@app.post("/api/auth/register", response_model=AuthResponse)
async def register(user_data: UserCreate):
    users = load_data(USERS_FILE)
    
    if user_data.email in users:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if phone number is already registered
    for existing_user in users.values():
        if isinstance(existing_user, dict) and existing_user.get("phone_number") == user_data.phone_number:
            raise HTTPException(status_code=400, detail="Phone number already registered")
    
    user_id = generate_user_id()
    hashed_password = get_password_hash(user_data.password)
    
    user = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "phone_number": user_data.phone_number,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Initialize user wallet
    wallets = load_data("user_wallets.json", default={})
    wallets[user_data.phone_number] = {
        "balance": 0.0,
        "equity": 0.0,
        "currency": "KES"
    }
    
    users[user_data.email] = user
    save_data(users, USERS_FILE)
    save_data(wallets, "user_wallets.json")
    
    # Log registration activity
    log_user_activity(user_data.phone_number, "registration", 0, "User registered successfully")
    
    access_token = create_access_token(
        data={"sub": user_data.email}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return AuthResponse(
        success=True,
        message="User registered successfully",
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**{k: v for k, v in user.items() if k != 'hashed_password'})
    )

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(login_data: UserLogin):
    users = load_data(USERS_FILE)
    
    print(f"Login attempt for email: {login_data.email}")
    print(f"Available users: {list(users.keys())}")
    
    user = users.get(login_data.email)
    
    if not user:
        print(f"User not found: {login_data.email}")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not verify_password(login_data.password, user["hashed_password"]):
        print("Password verification failed")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(
        data={"sub": user["email"]}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    print(f"Login successful for: {user['email']}")
    
    return AuthResponse(
        success=True,
        message="Login successful",
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**{k: v for k, v in user.items() if k != 'hashed_password'})
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**{k: v for k, v in current_user.items() if k != 'hashed_password'})

# Wallet endpoints
@app.get("/api/wallet/balance", response_model=WalletData)
async def get_wallet_balance(current_user: dict = Depends(get_current_user)):
    wallets = load_data("user_wallets.json", default={})
    user_wallet = wallets.get(current_user["phone_number"], {"balance": 0, "equity": 0, "currency": "KES"})
    
    # Update equity based on investments
    update_investment_values(current_user["phone_number"])
    
    return WalletData(**user_wallet)

@app.post("/api/wallet/deposit", response_model=TransactionResponse)
async def deposit_funds(deposit_data: DepositRequest, current_user: dict = Depends(get_current_user)):
    if deposit_data.phone_number != current_user["phone_number"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    wallets = load_data("user_wallets.json", default={})
    user_wallet = wallets.get(current_user["phone_number"], {"balance": 0, "equity": 0, "currency": "KES"})
    
    user_wallet["balance"] += deposit_data.amount
    user_wallet["equity"] += deposit_data.amount
    
    wallets[current_user["phone_number"]] = user_wallet
    save_data(wallets, "user_wallets.json")
    
    log_user_activity(
        current_user["phone_number"], 
        "deposit", 
        deposit_data.amount, 
        f"Deposit of KSh {deposit_data.amount}"
    )
    
    return TransactionResponse(
        success=True,
        message="Deposit successful",
        new_balance=user_wallet["balance"],
        new_equity=user_wallet["equity"],
        transaction_id=f"DEP{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )

@app.post("/api/wallet/withdraw", response_model=TransactionResponse)
async def withdraw_funds(withdraw_data: WithdrawRequest, current_user: dict = Depends(get_current_user)):
    if withdraw_data.phone_number != current_user["phone_number"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    wallets = load_data("user_wallets.json", default={})
    user_wallet = wallets.get(current_user["phone_number"], {"balance": 0, "equity": 0, "currency": "KES"})
    
    if user_wallet["balance"] < withdraw_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    user_wallet["balance"] -= withdraw_data.amount
    user_wallet["equity"] -= withdraw_data.amount
    
    wallets[current_user["phone_number"]] = user_wallet
    save_data(wallets, "user_wallets.json")
    
    log_user_activity(
        current_user["phone_number"], 
        "withdraw", 
        withdraw_data.amount, 
        f"Withdrawal of KSh {withdraw_data.amount}"
    )
    
    return TransactionResponse(
        success=True,
        message="Withdrawal successful",
        new_balance=user_wallet["balance"],
        new_equity=user_wallet["equity"],
        transaction_id=f"WD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )

@app.get("/api/wallet/pnl", response_model=PnLData)
async def get_pnl_data(current_user: dict = Depends(get_current_user)):
    """Get profit and loss data for the user"""
    try:
        # Get user investments
        investments = load_data("user_investments.json", default={})
        user_investments = [
            inv for inv in investments.values() 
            if inv["user_phone"] == current_user["phone_number"] and inv["status"] == "active"
        ]
        
        # Calculate total profit/loss
        total_profit_loss = sum(inv["profit_loss"] for inv in user_investments)
        total_invested = sum(inv["invested_amount"] for inv in user_investments)
        
        # Calculate percentage
        if total_invested > 0:
            percentage = (total_profit_loss / total_invested) * 100
        else:
            percentage = 0.0
        
        # Determine trend
        trend = "up" if total_profit_loss >= 0 else "down"
        
        return PnLData(
            profit_loss=total_profit_loss,
            percentage=percentage,
            trend=trend
        )
        
    except Exception as e:
        print(f"Error calculating PnL: {e}")
        # Return zero PnL if there's an error
        return PnLData(
            profit_loss=0.0,
            percentage=0.0,
            trend="up"
        )

# Investment endpoints
@app.post("/api/investments/buy")
async def buy_investment(investment_data: InvestmentRequest, current_user: dict = Depends(get_current_user)):
    if investment_data.phone_number != current_user["phone_number"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    wallets = load_data("user_wallets.json", default={})
    user_wallet = wallets.get(current_user["phone_number"], {"balance": 0, "equity": 0, "currency": "KES"})
    
    if user_wallet["balance"] < investment_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    assets = generate_dynamic_prices()
    asset = next((a for a in assets if a["id"] == investment_data.asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    units = investment_data.amount / asset["current_price"]
    
    investments = load_data("user_investments.json", default={})
    investment_id = get_next_id(investments)
    
    investment = {
        "id": investment_id,
        "user_phone": current_user["phone_number"],
        "asset_id": investment_data.asset_id,
        "asset_name": asset["name"],
        "invested_amount": investment_data.amount,
        "current_value": investment_data.amount,
        "units": units,
        "entry_price": asset["current_price"],
        "current_price": asset["current_price"],
        "profit_loss": 0.0,
        "profit_loss_percentage": 0.0,
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
    
    investments[investment_id] = investment
    save_data(investments, "user_investments.json")
    
    user_wallet["balance"] -= investment_data.amount
    wallets[current_user["phone_number"]] = user_wallet
    save_data(wallets, "user_wallets.json")
    
    log_user_activity(
        current_user["phone_number"], 
        "investment", 
        investment_data.amount, 
        f"Investment in {asset['name']} - {units:.4f} units"
    )
    
    return {
        "success": True,
        "message": f"Investment in {asset['name']} successful",
        "investment": investment,
        "new_balance": user_wallet["balance"]
    }

# Market data endpoints
@app.get("/api/assets/market", response_model=List[Asset])
async def get_market_assets():
    return generate_dynamic_prices()

@app.get("/api/investments/my", response_model=List[UserInvestment])
async def get_my_investments(current_user: dict = Depends(get_current_user)):
    investments = load_data("user_investments.json", default={})
    user_investments = [
        inv for inv in investments.values() 
        if inv["user_phone"] == current_user["phone_number"] and inv["status"] == "active"
    ]
    
    update_investment_values(current_user["phone_number"])
    
    return user_investments

@app.get("/api/activities/my", response_model=List[UserActivity])
async def get_my_activities(current_user: dict = Depends(get_current_user)):
    activities = load_data(USER_ACTIVITY_FILE, default={})
    user_activities = [
        activity for activity in activities.values() 
        if activity["user_phone"] == current_user["phone_number"]
    ]
    user_activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return user_activities[:20]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)