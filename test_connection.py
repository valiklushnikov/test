
import logging
from pybit.unified_trading import HTTP

# Вставьте ваши ключи сюда для проверки
API_KEY = "5Oe18HoCVHkSK2wdWQ"
API_SECRET = ""

logging.basicConfig(level=logging.DEBUG)

def test_bybit():
    print("-" * 50)
    print("Testing Bybit Connection...")
    print("-" * 50)
    
    try:
        # 1. Init Session
        print(f"1. Initializing HTTP session (testnet=False)...")
        session = HTTP(
            testnet=False,
            api_key=API_KEY,
            api_secret=API_SECRET,
            recv_window=10000
        )
        print("   -> Session object created successfully.")
        
        # 2. Test Key Info (Permissions)
        print("\n2. Requesting get_api_key_information()...")
        key_info = session.get_api_key_information()
        print("   -> Success! Key Info response:")
        print(key_info)
        
        # 3. Test Wallet Balance
        print("\n3. Requesting get_wallet_balance(accountType='UNIFIED')...")
        balance = session.get_wallet_balance(accountType="UNIFIED")
        print("   -> Success! Balance response:")
        print(balance)
        
        print("-" * 50)
        print("TEST PASSED: Connection works correctly.")
        print("-" * 50)
        
    except Exception as e:
        print("\n" + "!" * 50)
        print("TEST FAILED with Exception:")
        print(f"{type(e).__name__}: {str(e)}")
        print("!" * 50)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bybit()
