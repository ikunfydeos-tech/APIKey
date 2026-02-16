import sys
sys.path.insert(0, '.')

from database import SessionLocal, engine
from models import User
from auth import get_password_hash

# Test database connection
print("Testing database connection...")
try:
    db = SessionLocal()
    print("Database connection successful!")
    
    # Check existing users
    users = db.query(User).all()
    print(f"Existing users: {len(users)}")
    
    # Try to create a test user
    print("\nCreating test user...")
    hashed_password = get_password_hash("Test123456")
    new_user = User(
        username="testuser2",
        email="test2@example.com",
        password_hash=hashed_password,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f"User created successfully! ID: {new_user.id}")
    
    # Clean up - delete the test user
    db.delete(new_user)
    db.commit()
    print("Test user deleted.")
    
    db.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
