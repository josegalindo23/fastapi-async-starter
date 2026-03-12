# test_security.py (temporal)
from app.core.security import get_password_hash, verify_password, create_access_token

# Test 1: Hash
hashed = get_password_hash("test123")
print(f"Hashed: {hashed}")

# Test 2: Verify
is_valid = verify_password("test123", hashed)
print(f"Valid: {is_valid}")  # True

# Test 3: Token
token = create_access_token({"sub": "user_123"})
print(f"Token: {token[:50]}...")