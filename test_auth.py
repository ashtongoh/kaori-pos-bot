"""
Test script to check database connection and authorization
"""
import sys
from pathlib import Path

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import Database

def test_database_connection():
    """Test if database connection works"""
    print("Testing database connection...")

    db = Database()

    # Test 1: Check if we can query authorized users
    print("\n1. Testing authorized_users table...")
    try:
        response = db.client.table("authorized_users").select("*").execute()
        print(f"✅ Successfully connected to database")
        print(f"   Found {len(response.data)} authorized users:")
        for user in response.data:
            print(f"   - Telegram ID: {user.get('telegram_id')}, Username: @{user.get('username')}, Name: {user.get('full_name')}")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False

    # Test 2: Check menu items table
    print("\n2. Testing menu_items table...")
    try:
        items = db.get_menu_items()
        print(f"✅ Found {len(items)} menu items")
        for item in items:
            print(f"   - {item.get('name')} ({item.get('size')}): ${item.get('price')}")
    except Exception as e:
        print(f"❌ Error fetching menu items: {e}")

    # Test 3: Prompt user to add their Telegram ID
    print("\n3. Authorization test:")
    telegram_id = input("Enter your Telegram ID to check authorization (or press Enter to skip): ").strip()

    if telegram_id:
        try:
            telegram_id = int(telegram_id)
            is_authorized = db.is_user_authorized(telegram_id)

            if is_authorized:
                print(f"✅ Telegram ID {telegram_id} is AUTHORIZED")
            else:
                print(f"❌ Telegram ID {telegram_id} is NOT authorized")
                print(f"\nTo authorize this user, run the following SQL in Supabase:")
                print(f"\nINSERT INTO authorized_users (telegram_id, username, full_name)")
                print(f"VALUES ({telegram_id}, 'your_username', 'Your Name');")
        except ValueError:
            print("❌ Invalid Telegram ID format")

    return True

if __name__ == "__main__":
    print("="*60)
    print("Kori POS Bot - Database Connection Test")
    print("="*60)

    success = test_database_connection()

    print("\n" + "="*60)
    if success:
        print("✅ Database connection test completed")
    else:
        print("❌ Database connection test failed")
    print("="*60)
