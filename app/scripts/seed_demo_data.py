# app/scripts/seed_demo_data.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.wallet import Wallet
from app.models.investment import Investment
from app.models.transaction import Transaction
from datetime import datetime, timedelta
import random

def create_demo_user(db: Session):
    """Create or update demo user with comprehensive data"""
    
    # Check if demo user already exists
    demo_user = db.query(User).filter(User.email == "demo@pesaprime.com").first()
    
    if not demo_user:
        # Create demo user
        demo_user = User(
            name="Demo User",
            email="demo@pesaprime.com",
            phone_number="+254712345678",
            created_at=datetime.utcnow()
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print("✅ Demo user created")
    else:
        print("✅ Demo user already exists")
    
    return demo_user

def create_demo_wallet(db: Session, user_id: int):
    """Create or update demo wallet"""
    
    demo_wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    
    if not demo_wallet:
        demo_wallet = Wallet(
            user_id=user_id,
            balance=25000.00,
            equity=28750.00,
            currency="KES"
        )
        db.add(demo_wallet)
        print("✅ Demo wallet created")
    else:
        # Update existing wallet with demo data
        demo_wallet.balance = 25000.00
        demo_wallet.equity = 28750.00
        demo_wallet.currency = "KES"
        print("✅ Demo wallet updated")
    
    db.commit()
    return demo_wallet

def create_demo_transactions(db: Session, user_id: int):
    """Create demo transaction history"""
    
    # Clear existing demo transactions
    db.query(Transaction).filter(Transaction.user_id == user_id).delete()
    
    transactions_data = [
        {
            "type": "deposit",
            "amount": 20000.00,
            "description": "Initial deposit via M-Pesa",
            "timestamp": datetime.utcnow() - timedelta(days=30)
        },
        {
            "type": "deposit", 
            "amount": 10000.00,
            "description": "Additional funding",
            "timestamp": datetime.utcnow() - timedelta(days=15)
        },
        {
            "type": "withdrawal",
            "amount": 5000.00,
            "description": "Emergency withdrawal", 
            "timestamp": datetime.utcnow() - timedelta(days=10)
        },
        {
            "type": "investment",
            "amount": 8000.00,
            "description": "BTC Investment",
            "timestamp": datetime.utcnow() - timedelta(days=8)
        },
        {
            "type": "investment",
            "amount": 6000.00,
            "description": "ETH Investment",
            "timestamp": datetime.utcnow() - timedelta(days=7)
        },
        {
            "type": "investment", 
            "amount": 4000.00,
            "description": "Apple Stock Investment",
            "timestamp": datetime.utcnow() - timedelta(days=5)
        },
        {
            "type": "withdrawal",
            "amount": 3000.00,
            "description": "Monthly expenses",
            "timestamp": datetime.utcnow() - timedelta(days=3)
        },
        {
            "type": "bonus",
            "amount": 1000.00,
            "description": "Welcome bonus",
            "timestamp": datetime.utcnow() - timedelta(days=25)
        },
        {
            "type": "bonus",
            "amount": 500.00,
            "description": "Referral bonus", 
            "timestamp": datetime.utcnow() - timedelta(days=12)
        },
        {
            "type": "deposit",
            "amount": 7500.00,
            "description": "Salary deposit",
            "timestamp": datetime.utcnow() - timedelta(days=2)
        }
    ]
    
    for tx_data in transactions_data:
        transaction = Transaction(
            user_id=user_id,
            type=tx_data["type"],
            amount=tx_data["amount"],
            description=tx_data["description"],
            timestamp=tx_data["timestamp"],
            status="completed",
            currency="KES"
        )
        db.add(transaction)
    
    db.commit()
    print("✅ Demo transactions created")

def create_demo_investments(db: Session, user_id: int):
    """Create demo investment portfolio"""
    
    # Clear existing demo investments
    db.query(Investment).filter(Investment.user_id == user_id).delete()
    
    investments_data = [
        {
            "asset_id": "1",
            "asset_name": "Bitcoin",
            "invested_amount": 8000.00,
            "current_value": 9250.00,
            "units": 0.18,
            "profit_loss": 1250.00,
            "profit_loss_percentage": 15.63,
            "created_at": datetime.utcnow() - timedelta(days=8)
        },
        {
            "asset_id": "2", 
            "asset_name": "Ethereum",
            "invested_amount": 6000.00,
            "current_value": 6800.00,
            "units": 2.1,
            "profit_loss": 800.00,
            "profit_loss_percentage": 13.33,
            "created_at": datetime.utcnow() - timedelta(days=7)
        },
        {
            "asset_id": "3",
            "asset_name": "Apple Inc", 
            "invested_amount": 4000.00,
            "current_value": 4200.00,
            "units": 21.5,
            "profit_loss": 200.00,
            "profit_loss_percentage": 5.00,
            "created_at": datetime.utcnow() - timedelta(days=5)
        },
        {
            "asset_id": "4",
            "asset_name": "EUR/USD",
            "invested_amount": 3000.00, 
            "current_value": 3050.00,
            "units": 2765,
            "profit_loss": 50.00,
            "profit_loss_percentage": 1.67,
            "created_at": datetime.utcnow() - timedelta(days=3)
        }
    ]
    
    for inv_data in investments_data:
        investment = Investment(
            user_id=user_id,
            asset_id=inv_data["asset_id"],
            asset_name=inv_data["asset_name"],
            invested_amount=inv_data["invested_amount"],
            current_value=inv_data["current_value"],
            units=inv_data["units"],
            profit_loss=inv_data["profit_loss"],
            profit_loss_percentage=inv_data["profit_loss_percentage"],
            status="active",
            created_at=inv_data["created_at"]
        )
        db.add(investment)
    
    db.commit()
    print("✅ Demo investments created")

def seed_demo_data(db: Session):
    """Main function to seed all demo data"""
    try:
        print("🚀 Seeding demo data...")
        
        # Create demo user
        demo_user = create_demo_user(db)
        
        # Create demo wallet
        demo_wallet = create_demo_wallet(db, demo_user.id)
        
        # Create demo transactions
        create_demo_transactions(db, demo_user.id)
        
        # Create demo investments
        create_demo_investments(db, demo_user.id)
        
        print("🎉 Demo data seeding completed successfully!")
        print(f"📧 Demo User Email: {demo_user.email}")
        print(f"📱 Demo User Phone: {demo_user.phone_number}")
        print(f"💰 Demo Wallet Balance: {demo_wallet.balance} {demo_wallet.currency}")
        
    except Exception as e:
        print(f"❌ Error seeding demo data: {e}")
        db.rollback()
        raise

# Run this from your main.py or create a separate script
if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    seed_demo_data(db)