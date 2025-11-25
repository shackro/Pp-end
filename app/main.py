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
import aiohttp
import asyncio
from app.routes.activities import router as activities_router
from app.routes.auth import router as auth_router
from app.routes.wallet import router as wallet_router
from app.routes.investments import router as investments_router

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["md5_crypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "5L5vfBJhjFPBGfMtXh_m5AjPVBXNTXCcPyqlYyJTsOU")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "70"))

# Get allowed origins from environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://pesaprime.vercel.app")
ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:3000",
    "https://pesaprime.vercel.app"
]

origins = [
     FRONTEND_URL,
    "https://pesaprime.vercel.app",  # Vercel frontend URL
    "http://localhost:3000",         # local dev URL (Vite)
]

# File-based storage
USERS_FILE = "users.json"
USER_ACTIVITY_FILE = "user_activity.json"
USER_WALLETS_FILE = "user_wallets.json"
USER_INVESTMENTS_FILE = "user_investments.json"

app = FastAPI(
    title="Pesdaprime API",
    description="Personal Finance Dashboard Backend",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use absolute paths for production
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
USER_ACTIVITY_FILE = os.path.join(BASE_DIR, "user_activity.json")
USER_WALLETS_FILE = os.path.join(BASE_DIR, "user_wallets.json")
USER_INVESTMENTS_FILE = os.path.join(BASE_DIR, "user_investments.json")


app.include_router(auth_router, prefix="/api/auth")
app.include_router(wallet_router, prefix="/api/wallet")
app.include_router(investments_router, prefix="/api/investments")
app.include_router(activities_router, prefix="/api/activities")

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
    hourly_income: float
    min_investment: float
    duration: int

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


class PnLData(BaseModel):
    profit_loss: float
    percentage: float
    trend: str


# PRODUCTION ASSETS DATA
PRODUCTION_ASSETS = {
    'crypto': [
        {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC', 'type': 'crypto', 'coingecko_id': 'bitcoin', 'min_investment_kes': 450, 'hourly_income_range': [90, 150], 'duration': 24},
        {'id': 'ethereum', 'name': 'Ethereum', 'symbol': 'ETH', 'type': 'crypto', 'coingecko_id': 'ethereum', 'min_investment_kes': 450, 'hourly_income_range': [85, 140], 'duration': 24},
        {'id': 'bnb', 'name': 'Binance Coin', 'symbol': 'BNB', 'type': 'crypto', 'coingecko_id': 'binancecoin', 'min_investment_kes': 450, 'hourly_income_range': [80, 130], 'duration': 24},
        {'id': 'solana', 'name': 'Solana', 'symbol': 'SOL', 'type': 'crypto', 'coingecko_id': 'solana', 'min_investment_kes': 450, 'hourly_income_range': [95, 160], 'duration': 24},
        {'id': 'xrp', 'name': 'Ripple', 'symbol': 'XRP', 'type': 'crypto', 'coingecko_id': 'ripple', 'min_investment_kes': 450, 'hourly_income_range': [70, 120], 'duration': 24},
        {'id': 'cardano', 'name': 'Cardano', 'symbol': 'ADA', 'type': 'crypto', 'coingecko_id': 'cardano', 'min_investment_kes': 450, 'hourly_income_range': [65, 110], 'duration': 24},
        {'id': 'dogecoin', 'name': 'Dogecoin', 'symbol': 'DOGE', 'type': 'crypto', 'coingecko_id': 'dogecoin', 'min_investment_kes': 450, 'hourly_income_range': [60, 100], 'duration': 24},
        {'id': 'polkadot', 'name': 'Polkadot', 'symbol': 'DOT', 'type': 'crypto', 'coingecko_id': 'polkadot', 'min_investment_kes': 450, 'hourly_income_range': [75, 125], 'duration': 24},
        {'id': 'litecoin', 'name': 'Litecoin', 'symbol': 'LTC', 'type': 'crypto', 'coingecko_id': 'litecoin', 'min_investment_kes': 450, 'hourly_income_range': [70, 115], 'duration': 24},
        {'id': 'chainlink', 'name': 'Chainlink', 'symbol': 'LINK', 'type': 'crypto', 'coingecko_id': 'chainlink', 'min_investment_kes': 450, 'hourly_income_range': [72, 118], 'duration': 24}
    ],
    'forex': [
        {'id': 'eur-usd', 'name': 'EUR/USD', 'symbol': 'EURUSD', 'type': 'forex', 'forex_symbol': 'EURUSD', 'min_investment_kes': 500, 'hourly_income_range': [100, 180], 'duration': 24},
        {'id': 'gbp-usd', 'name': 'GBP/USD', 'symbol': 'GBPUSD', 'type': 'forex', 'forex_symbol': 'GBPUSD', 'min_investment_kes': 500, 'hourly_income_range': [95, 170], 'duration': 24},
        {'id': 'usd-jpy', 'name': 'USD/JPY', 'symbol': 'USDJPY', 'type': 'forex', 'forex_symbol': 'USDJPY', 'min_investment_kes': 500, 'hourly_income_range': [90, 160], 'duration': 24},
        {'id': 'usd-chf', 'name': 'USD/CHF', 'symbol': 'USDCHF', 'type': 'forex', 'forex_symbol': 'USDCHF', 'min_investment_kes': 500, 'hourly_income_range': [85, 150], 'duration': 24},
        {'id': 'aud-usd', 'name': 'AUD/USD', 'symbol': 'AUDUSD', 'type': 'forex', 'forex_symbol': 'AUDUSD', 'min_investment_kes': 500, 'hourly_income_range': [92, 165], 'duration': 24},
        {'id': 'usd-cad', 'name': 'USD/CAD', 'symbol': 'USDCAD', 'type': 'forex', 'forex_symbol': 'USDCAD', 'min_investment_kes': 500, 'hourly_income_range': [88, 155], 'duration': 24},
        {'id': 'nzd-usd', 'name': 'NZD/USD', 'symbol': 'NZDUSD', 'type': 'forex', 'forex_symbol': 'NZDUSD', 'min_investment_kes': 500, 'hourly_income_range': [82, 145], 'duration': 24},
        {'id': 'eur-gbp', 'name': 'EUR/GBP', 'symbol': 'EURGBP', 'type': 'forex', 'forex_symbol': 'EURGBP', 'min_investment_kes': 500, 'hourly_income_range': [80, 140], 'duration': 24},
        {'id': 'eur-jpy', 'name': 'EUR/JPY', 'symbol': 'EURJPY', 'type': 'forex', 'forex_symbol': 'EURJPY', 'min_investment_kes': 500, 'hourly_income_range': [105, 190], 'duration': 24},
        {'id': 'gbp-jpy', 'name': 'GBP/JPY', 'symbol': 'GBPJPY', 'type': 'forex', 'forex_symbol': 'GBPJPY', 'min_investment_kes': 500, 'hourly_income_range': [110, 200], 'duration': 24}
    ],
    'futures': [
        {'id': 'gold', 'name': 'Gold Futures', 'symbol': 'XAUUSD', 'type': 'commodity', 'symbol_key': 'GC=F', 'min_investment_kes': 550, 'hourly_income_range': [120, 220], 'duration': 24},
        {'id': 'silver', 'name': 'Silver Futures', 'symbol': 'XAGUSD', 'type': 'commodity', 'symbol_key': 'SI=F', 'min_investment_kes': 550, 'hourly_income_range': [95, 180], 'duration': 24},
        {'id': 'oil', 'name': 'Crude Oil WTI', 'symbol': 'USOIL', 'type': 'commodity', 'symbol_key': 'CL=F', 'min_investment_kes': 550, 'hourly_income_range': [110, 200], 'duration': 24},
        {'id': 'sp500', 'name': 'S&P 500', 'symbol': 'SPX', 'type': 'futures', 'symbol_key': 'ES=F', 'min_investment_kes': 600, 'hourly_income_range': [130, 220], 'duration': 24},
        {'id': 'nasdaq', 'name': 'Nasdaq 100', 'symbol': 'NAS100', 'type': 'futures', 'symbol_key': 'NQ=F', 'min_investment_kes': 600, 'hourly_income_range': [140, 220], 'duration': 24},
        {'id': 'dowjones', 'name': 'Dow Jones', 'symbol': 'DJI', 'type': 'futures', 'symbol_key': 'YM=F', 'min_investment_kes': 600, 'hourly_income_range': [125, 210], 'duration': 24},
        {'id': 'copper', 'name': 'Copper Futures', 'symbol': 'COPPER', 'type': 'commodity', 'symbol_key': 'HG=F', 'min_investment_kes': 500, 'hourly_income_range': [75, 150], 'duration': 24},
        {'id': 'naturalgas', 'name': 'Natural Gas', 'symbol': 'NATGAS', 'type': 'commodity', 'symbol_key': 'NG=F', 'min_investment_kes': 500, 'hourly_income_range': [65, 130], 'duration': 24}
    ],
    'stocks': [
        {'id': 'apple', 'name': 'Apple Inc', 'symbol': 'AAPL', 'type': 'stock', 'symbol_key': 'AAPL', 'min_investment_kes': 600, 'hourly_income_range': [125, 210], 'duration': 24},
        {'id': 'microsoft', 'name': 'Microsoft', 'symbol': 'MSFT', 'type': 'stock', 'symbol_key': 'MSFT', 'min_investment_kes': 600, 'hourly_income_range': [140, 220], 'duration': 24},
        {'id': 'google', 'name': 'Alphabet', 'symbol': 'GOOGL', 'type': 'stock', 'symbol_key': 'GOOGL', 'min_investment_kes': 600, 'hourly_income_range': [120, 200], 'duration': 24},
        {'id': 'amazon', 'name': 'Amazon', 'symbol': 'AMZN', 'type': 'stock', 'symbol_key': 'AMZN', 'min_investment_kes': 600, 'hourly_income_range': [135, 215], 'duration': 24},
        {'id': 'tesla', 'name': 'Tesla Inc', 'symbol': 'TSLA', 'type': 'stock', 'symbol_key': 'TSLA', 'min_investment_kes': 600, 'hourly_income_range': [145, 220], 'duration': 24},
        {'id': 'meta', 'name': 'Meta Platforms', 'symbol': 'META', 'type': 'stock', 'symbol_key': 'META', 'min_investment_kes': 600, 'hourly_income_range': [150, 220], 'duration': 24},
        {'id': 'nvidia', 'name': 'NVIDIA Corp', 'symbol': 'NVDA', 'type': 'stock', 'symbol_key': 'NVDA', 'min_investment_kes': 650, 'hourly_income_range': [160, 220], 'duration': 24},
        {'id': 'berkshire', 'name': 'Berkshire Hathaway', 'symbol': 'BRK.B', 'type': 'stock', 'symbol_key': 'BRK-B', 'min_investment_kes': 550, 'hourly_income_range': [100, 180], 'duration': 24},
        {'id': 'netflix', 'name': 'Netflix Inc', 'symbol': 'NFLX', 'type': 'stock', 'symbol_key': 'NFLX', 'min_investment_kes': 600, 'hourly_income_range': [130, 210], 'duration': 24},
        {'id': 'salesforce', 'name': 'Salesforce Inc', 'symbol': 'CRM', 'type': 'stock', 'symbol_key': 'CRM', 'min_investment_kes': 600, 'hourly_income_range': [125, 205], 'duration': 24}
    ]
}

TODAYS_BASE_PRICES = {
    'BTC': 92036.00, 'ETH': 3016.97, 'BNB': 321.78, 'SOL': 107.89,
    'XRP': 0.6234, 'ADA': 0.4821, 'DOGE': 0.0876, 'DOT': 7.234,
    'LTC': 72.89, 'LINK': 15.67, 'EURUSD': 1.1591, 'GBPUSD': 1.2678,
    'USDJPY': 148.25, 'USDCHF': 0.8689, 'AUDUSD': 0.6523, 'USDCAD': 1.3521,
    'NZDUSD': 0.6123, 'EURGBP': 0.8567, 'EURJPY': 160.89, 'GBPJPY': 188.34,
    'XAUUSD': 1987.45, 'XAGUSD': 23.15, 'USOIL': 78.45, 'SPX': 4950.75,
    'NAS100': 17540.50, 'DJI': 38500.25, 'COPPER': 3.85, 'NATGAS': 2.45,
    'AAPL': 189.45, 'MSFT': 378.85, 'GOOGL': 138.45, 'AMZN': 154.75,
    'TSLA': 245.60, 'META': 345.25, 'NVDA': 495.75, 'BRK.B': 362.50,
    'NFLX': 485.32, 'CRM': 278.90
}


# Currency exchange rates (to KES)
CURRENCY_RATES = {
    "KES": 1.0,
    "USD": 0.0078,  # 1 KES = 0.0078 USD
    "EUR": 0.0072,  # 1 KES = 0.0072 EUR
    "GBP": 0.0062,  # 1 KES = 0.0062 GBP
    "ZAR": 0.15,    # 1 KES = 0.15 ZAR
    "UGX": 28.5,    # 1 KES = 28.5 UGX
    "TZS": 20.1,    # 1 KES = 20.1 TZS
}

# Storage functions
@app.on_event("startup")
async def startup_event():
    """Ensure required files exist on startup"""
    required_files = [USERS_FILE, USER_ACTIVITY_FILE, USER_WALLETS_FILE, USER_INVESTMENTS_FILE]
    for file_path in required_files:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)
            print(f"Created {file_path}")

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

async def update_investment_values(user_phone: str):
    """Update investment values based on current market prices"""
    investments = load_data(USER_INVESTMENTS_FILE, default={})
    current_assets = await generate_dynamic_prices()  # Add await here
    
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
    
    save_data(investments, USER_INVESTMENTS_FILE)

# REAL-TIME PRICE FETCHING FUNCTIONS
async def fetch_real_crypto_price(coin_id: str, symbol: str):
    """Fetch real crypto prices from CoinGecko with fallback to today's prices"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if coin_id in data:
                        return {
                            'price': data[coin_id]['usd'],
                            'change_24h': data[coin_id].get('usd_24h_change', 0)
                        }
    except Exception as e:
        print(f"Error fetching crypto price for {coin_id}: {e}")
    
    # Fallback to today's prices with small random variation
    base_price = TODAYS_BASE_PRICES.get(symbol, 100)
    change = random.uniform(-0.01, 0.01)  # Small variation
    return {
        'price': base_price * (1 + change),
        'change_24h': change * 100
    }

async def fetch_real_forex_price(forex_pair: str, symbol: str):
    """Fetch real forex prices with fallback to today's prices"""
    try:
        # Using free forex API
        url = f"https://api.frankfurter.app/latest?from={forex_pair[:3]}&to={forex_pair[3:]}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'rates' in data and forex_pair[3:] in data['rates']:
                        price = data['rates'][forex_pair[3:]]
                        return {
                            'price': price,
                            'change_24h': random.uniform(-0.5, 0.5)  # Simulated change
                        }
    except Exception as e:
        print(f"Error fetching forex price for {forex_pair}: {e}")
    
    # Fallback to today's prices
    base_price = TODAYS_BASE_PRICES.get(symbol, 1.0)
    change = random.uniform(-0.005, 0.005)  # Small variation for forex
    return {
        'price': base_price * (1 + change),
        'change_24h': change * 100
    }

async def fetch_real_stock_price(symbol: str):
    """Fetch real stock prices with fallback to today's prices"""
    try:
        # Using Yahoo Finance alternative
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        if 'meta' in result and 'regularMarketPrice' in result['meta']:
                            price = result['meta']['regularMarketPrice']
                            previous_close = result['meta'].get('previousClose', price)
                            change_24h = ((price - previous_close) / previous_close) * 100
                            return {
                                'price': price,
                                'change_24h': change_24h
                            }
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {e}")
    
    # Fallback to today's prices
    base_price = TODAYS_BASE_PRICES.get(symbol, 100)
    change = random.uniform(-0.02, 0.02)
    return {
        'price': base_price * (1 + change),
        'change_24h': change * 100
    }

async def generate_real_time_prices():
    """Generate real-time prices for all assets with proper fallbacks"""
    assets_with_prices = []
    
    # Combine all production assets
    all_assets = []
    for category_assets in PRODUCTION_ASSETS.values():
        all_assets.extend(category_assets)
    
    # Fetch prices concurrently
    tasks = []
    for asset in all_assets:
        if asset['type'] == 'crypto' and 'coingecko_id' in asset:
            tasks.append(fetch_real_crypto_price(asset['coingecko_id'], asset['symbol']))
        elif asset['type'] == 'forex' and 'forex_symbol' in asset:
            tasks.append(fetch_real_forex_price(asset['forex_symbol'], asset['symbol']))
        elif asset['type'] == 'stock' and 'symbol_key' in asset:
            tasks.append(fetch_real_stock_price(asset['symbol_key']))
        else:
            # For commodities and futures, use today's prices with variation
            base_price = TODAYS_BASE_PRICES.get(asset['symbol'], 100)
            change = random.uniform(-0.01, 0.01)
            async def dummy_price():
                return {
                    'price': base_price * (1 + change),
                    'change_24h': change * 100
                }
            tasks.append(dummy_price())
    
    price_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, asset in enumerate(all_assets):
        price_data = price_results[i] if i < len(price_results) else None
        
        if price_data and not isinstance(price_data, Exception):
            current_price = price_data['price']
            change_percentage = price_data.get('change_24h', random.uniform(-2, 2))
        else:
            # Final fallback to today's base prices
            base_price = TODAYS_BASE_PRICES.get(asset['symbol'], 100)
            change = random.uniform(-0.01, 0.01)
            current_price = base_price * (1 + change)
            change_percentage = change * 100
        
        # Calculate hourly income in KSH (120-350 KSH range)
        hourly_income_kes = random.uniform(120, 350)
        
        # Convert to USD for display if needed, but store in KSH
        hourly_income_usd = hourly_income_kes * CURRENCY_RATES["USD"]
        
        total_income_kes = hourly_income_kes * asset['duration']
        roi_percentage = (total_income_kes / asset['min_investment_kes']) * 100
        
        assets_with_prices.append({
            "id": asset["id"],
            "name": asset["name"],
            "symbol": asset["symbol"],
            "type": asset["type"],
            "current_price": round(current_price, 4),
            "change_percentage": round(change_percentage, 2),
            "moving_average": round(current_price * random.uniform(0.98, 1.02), 4),
            "trend": "up" if change_percentage >= 0 else "down",
            "chart_url": f"https://www.tradingview.com/chart/?symbol={asset['symbol']}",
            "hourly_income": round(hourly_income_kes, 2),  # Store in KSH
            "min_investment": asset['min_investment_kes'],  # In KSH
            "duration": asset["duration"],
            "total_income": round(total_income_kes, 2),  # In KSH
            "roi_percentage": round(roi_percentage, 1)
        })
    
    return assets_with_prices

async def generate_dynamic_prices():
    """Generate realistic dynamic prices with real-time data"""
    try:
        return await generate_real_time_prices()
    except Exception as e:
        print(f"Error generating real-time prices: {e}")
        # Fallback to simulated data with today's prices
        return await generate_fallback_prices()

async def generate_fallback_prices():
    """Fallback price generation using today's market prices"""
    assets_with_prices = []
    
    all_assets = []
    for category_assets in PRODUCTION_ASSETS.values():
        all_assets.extend(category_assets)
    
    for asset in all_assets:
        base_price = TODAYS_BASE_PRICES.get(asset['symbol'], 100)
        change = random.uniform(-0.01, 0.01)
        current_price = base_price * (1 + change)
        change_percentage = change * 100
        
        # Hourly income in KSH (120-350 range)
        hourly_income_kes = random.uniform(120, 350)
        total_income_kes = hourly_income_kes * asset['duration']
        roi_percentage = (total_income_kes / asset['min_investment_kes']) * 100
        
        assets_with_prices.append({
            "id": asset["id"],
            "name": asset["name"],
            "symbol": asset["symbol"],
            "type": asset["type"],
            "current_price": round(current_price, 4),
            "change_percentage": round(change_percentage, 2),
            "moving_average": round(current_price * random.uniform(0.98, 1.02), 4),
            "trend": "up" if change_percentage >= 0 else "down",
            "chart_url": f"https://www.tradingview.com/chart/?symbol={asset['symbol']}",
            "hourly_income": round(hourly_income_kes, 2),
            "min_investment": asset['min_investment_kes'],
            "duration": asset["duration"],
            "total_income": round(total_income_kes, 2),
            "roi_percentage": round(roi_percentage, 1)
        })
    
    return assets_with_prices

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
    wallets = load_data(USER_WALLETS_FILE, default={})
    wallets[user_data.phone_number] = {
        "balance": 5000.0,  # Start with 5000 KES
        "equity": 5000.0,
        "currency": "KES"
    }
    
    users[user_data.email] = user
    save_data(users, USERS_FILE)
    save_data(wallets, USER_WALLETS_FILE)
    
    # Log registration activity
    log_user_activity(user_data.phone_number, "registration", 0, "User registered successfully")
    log_user_activity(user_data.phone_number, "deposit", 5000, "Welcome bonus deposited")
    
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
@app.get("/api/wallet/balance/{phone_number}", response_model=WalletData)
async def get_wallet_balance(phone_number: str):
    wallets = load_data(USER_WALLETS_FILE, default={})
    user_wallet = wallets.get(phone_number, {"balance": 0, "equity": 0, "currency": "KES"})
    
    # Update equity based on investments
    await update_investment_values(phone_number)  # Add await here
    
    return WalletData(**user_wallet)

@app.post("/api/wallet/deposit", response_model=TransactionResponse)
async def deposit_funds(deposit_data: DepositRequest, current_user: dict = Depends(get_current_user)):
    if deposit_data.phone_number != current_user["phone_number"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    wallets = load_data(USER_WALLETS_FILE, default={})
    user_wallet = wallets.get(current_user["phone_number"], {"balance": 0, "equity": 0, "currency": "KES"})
    
    user_wallet["balance"] += deposit_data.amount
    user_wallet["equity"] += deposit_data.amount
    
    wallets[current_user["phone_number"]] = user_wallet
    save_data(wallets, USER_WALLETS_FILE)
    
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
    
    wallets = load_data(USER_WALLETS_FILE, default={})
    user_wallet = wallets.get(current_user["phone_number"], {"balance": 0, "equity": 0, "currency": "KES"})
    
    if user_wallet["balance"] < withdraw_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    user_wallet["balance"] -= withdraw_data.amount
    user_wallet["equity"] -= withdraw_data.amount
    
    wallets[current_user["phone_number"]] = user_wallet
    save_data(wallets, USER_WALLETS_FILE)
    
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
async def get_user_pnl(current_user: dict = Depends(get_current_user)):
    """Calculate user's overall PnL across active investments"""
    await update_investment_values(current_user["phone_number"])
    investments = load_data(USER_INVESTMENTS_FILE, default={})
    
    total_invested = 0
    total_current_value = 0
    
    for inv in investments.values():
        if inv["user_phone"] == current_user["phone_number"] and inv["status"] == "active":
            total_invested += inv.get("invested_amount", 0)
            total_current_value += inv.get("current_value", 0)
    
    if total_invested == 0:
        profit_loss = 0
        percentage = 0
        trend = "neutral"
    else:
        profit_loss = total_current_value - total_invested
        percentage = (profit_loss / total_invested) * 100
        trend = "up" if profit_loss >= 0 else "down"
    
    return PnLData(
        profit_loss=round(profit_loss, 2),
        percentage=round(percentage, 2),
        trend=trend
    )


# Investment endpoints
@app.post("/api/investments/buy")
async def buy_investment(investment_data: InvestmentRequest, current_user: dict = Depends(get_current_user)):
    if investment_data.phone_number != current_user["phone_number"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    wallets = load_data(USER_WALLETS_FILE, default={})
    user_wallet = wallets.get(current_user["phone_number"], {"balance": 0, "equity": 0, "currency": "KES"})
    
    # Convert investment amount to KES for validation
    amount_kes = investment_data.amount
    # Note: In your frontend, you'll convert the currency before sending
    
    if user_wallet["balance"] < amount_kes:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    assets = await generate_dynamic_prices()
    asset = next((a for a in assets if a["id"] == investment_data.asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Check minimum investment (already in KES)
    if amount_kes < asset["min_investment"]:
        raise HTTPException(status_code=400, detail=f"Minimum investment is {asset['min_investment']} KES")
    
    units = amount_kes / asset["current_price"]
    
    investments = load_data(USER_INVESTMENTS_FILE, default={})
    investment_id = get_next_id(investments)
    
    investment = {
        "id": investment_id,
        "user_phone": current_user["phone_number"],
        "asset_id": investment_data.asset_id,
        "asset_name": asset["name"],
        "invested_amount": amount_kes,
        "current_value": amount_kes,
        "units": units,
        "entry_price": asset["current_price"],
        "current_price": asset["current_price"],
        "hourly_income": asset["hourly_income"],
        "total_income": asset["total_income"],
        "duration": asset["duration"],
        "roi_percentage": asset["roi_percentage"],
        "profit_loss": 0.0,
        "profit_loss_percentage": 0.0,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "completion_time": (datetime.utcnow() + timedelta(hours=asset["duration"])).isoformat()
    }
    
    investments[investment_id] = investment
    save_data(investments, USER_INVESTMENTS_FILE)
    
    user_wallet["balance"] -= amount_kes
    wallets[current_user["phone_number"]] = user_wallet
    save_data(wallets, USER_WALLETS_FILE)
    
    log_user_activity(
        current_user["phone_number"], 
        "investment", 
        amount_kes, 
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
    return await generate_dynamic_prices()  # Add await here

@app.get("/api/investments/my/{phone_number}", response_model=List[UserInvestment])
async def get_my_investments(phone_number: str):
    investments = load_data(USER_INVESTMENTS_FILE, default={})
    user_investments = [
        inv for inv in investments.values() 
        if inv["user_phone"] == phone_number and inv["status"] == "active"
    ]
    
    await update_investment_values(phone_number)  # Add await here
    
    return user_investments

@app.get("/api/activities/my/{phone_number}", response_model=List[UserActivity])
async def get_my_activities(phone_number: str):
    activities = load_data(USER_ACTIVITY_FILE, default={})
    user_activities = [
        activity for activity in activities.values() 
        if activity["user_phone"] == phone_number
    ]
    user_activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return user_activities[:20]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
