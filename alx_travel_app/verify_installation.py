"""
Installation Verification Script
Run this script to verify that the ALX Travel App is properly set up.
"""

import sys
import os

def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires 3.8+")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    print("\nChecking dependencies...")
    required_packages = [
        'django',
        'rest_framework',
        'corsheaders',
        'celery',
        'redis',
        'requests',
        'dotenv'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            if package == 'rest_framework':
                __import__('rest_framework')
            elif package == 'corsheaders':
                __import__('corsheaders')
            elif package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"✅ {package} - Installed")
        except ImportError:
            print(f"❌ {package} - Not installed")
            all_installed = False
    
    return all_installed

def check_env_file():
    """Check if .env file exists."""
    print("\nChecking environment configuration...")
    if os.path.exists('.env'):
        print("✅ .env file - Found")
        
        # Check for required variables
        with open('.env', 'r') as f:
            content = f.read()
            required_vars = ['CHAPA_SECRET_KEY', 'DJANGO_SECRET_KEY']
            for var in required_vars:
                if var in content:
                    print(f"✅ {var} - Configured")
                else:
                    print(f"⚠️  {var} - Not found (please configure)")
        return True
    else:
        print("⚠️  .env file - Not found")
        print("   Run: cp .env.example .env")
        return False

def check_django_setup():
    """Check if Django is properly configured."""
    print("\nChecking Django setup...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')
        import django
        django.setup()
        print("✅ Django - Configured")
        
        # Check if migrations are needed
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        try:
            call_command('showmigrations', '--plan', stdout=out)
            print("✅ Migrations - System ready")
        except:
            print("⚠️  Migrations - Need to run: python manage.py migrate")
        
        return True
    except Exception as e:
        print(f"❌ Django setup - Error: {str(e)}")
        return False

def check_directory_structure():
    """Check if all required directories exist."""
    print("\nChecking directory structure...")
    required_dirs = [
        'alx_travel_app',
        'listings',
        'listings/migrations'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}/ - Exists")
        else:
            print(f"❌ {dir_path}/ - Not found")
            all_exist = False
    
    return all_exist

def check_key_files():
    """Check if all key files exist."""
    print("\nChecking key files...")
    required_files = [
        'manage.py',
        'requirements.txt',
        'listings/models.py',
        'listings/views.py',
        'listings/serializers.py',
        'listings/services.py',
        'listings/tasks.py',
        'listings/urls.py',
        'alx_travel_app/settings.py',
        'alx_travel_app/celery.py'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} - Exists")
        else:
            print(f"❌ {file_path} - Not found")
            all_exist = False
    
    return all_exist

def check_redis():
    """Check if Redis is accessible."""
    print("\nChecking Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis - Connected")
        return True
    except Exception as e:
        print(f"⚠️  Redis - Not accessible")
        print("   Make sure Redis is running: redis-server")
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("ALX Travel App - Installation Verification")
    print("=" * 60)
    
    checks = []
    
    # Run all checks
    checks.append(("Python Version", check_python_version()))
    checks.append(("Dependencies", check_dependencies()))
    checks.append(("Directory Structure", check_directory_structure()))
    checks.append(("Key Files", check_key_files()))
    checks.append(("Environment Config", check_env_file()))
    
    # Optional checks
    checks.append(("Django Setup", check_django_setup()))
    checks.append(("Redis Connection", check_redis()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<40} {status}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All checks passed! Your installation is complete.")
        print("\nNext steps:")
        print("1. python manage.py runserver")
        print("2. Visit http://localhost:8000/admin")
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")
        print("\nCommon fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Create .env file: cp .env.example .env")
        print("3. Run migrations: python manage.py migrate")
        print("4. Start Redis: redis-server")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
