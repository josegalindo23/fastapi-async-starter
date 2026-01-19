# final_check.py
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

async def check():
    print("=== PROJECT VERIFICATION  ===")
    
    checks = []
    
    # 1. Verify imports
    try:
        from app.main import app
        checks.append(("✅ App import", True))
    except Exception as e:
        checks.append((f"❌ App import: {e}", False))
    
    # 2. Verify models
    try:
        from app.models.users import User
        checks.append(("✅ Modelo User", True))
    except Exception as e:
        checks.append((f"❌ Modelo User: {e}", False))
    
    # 3. Verify services
    try:
        from app.services.user_service import pwd_context
        test_hash = pwd_context.hash("test")
        checks.append(("✅ Password hashing", True))
    except Exception as e:
        checks.append((f"❌ Password hashing: {e}", False))
    
    # 4. Verify routers
    print("\nResultados:")
    for check, passed in checks:
        print(check)
    
    # 5. Verify file structure
    print("\nEstructura de archivos:")
    required_files = [
        "app/__init__.py",
        "app/main.py", 
        "app/core/config.py",
        "app/models/users.py",
        "app/schemas/user.py",
        "app/services/user_service.py",
        "app/routers/users.py",
        "app/routers/health.py",
        "app/db/database.py",
        "app/db/base.py",
        ".gitignore",
        "requirements.txt",
        ".env.example",
        "README.md"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (FALTANTE)")
    
    return all(passed for _, passed in checks)

if __name__ == "__main__":
    success = asyncio.run(check())
    sys.exit(0 if success else 1)