#!/usr/bin/env python3
"""
Migration script from v1.0.0 to v2.0.0

This script handles the migration of data and configuration
from the legacy system to the new architecture.
"""

import os
import sys
import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

def backup_existing_data():
    """Create backup of existing data"""
    print("📦 Creating backup of existing data...")
    
    backup_dir = Path(f"backup_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)
    
    # Backup database
    if Path("logs/calls.db").exists():
        shutil.copy2("logs/calls.db", backup_dir / "calls.db")
        print(f"  ✅ Database backed up to {backup_dir}/calls.db")
    
    # Backup config
    if Path("config.py").exists():
        shutil.copy2("config.py", backup_dir / "config.py")
        print(f"  ✅ Config backed up to {backup_dir}/config.py")
    
    # Backup logs
    if Path("logs").exists():
        shutil.copytree("logs", backup_dir / "logs", dirs_exist_ok=True)
        print(f"  ✅ Logs backed up to {backup_dir}/logs/")
    
    return backup_dir

def migrate_database():
    """Migrate database schema from v1 to v2"""
    print("🗄️ Migrating database schema...")
    
    old_db_path = Path("logs/calls.db")
    new_db_path = Path("data/calls.db")
    
    if not old_db_path.exists():
        print("  ⚠️  No existing database found, skipping migration")
        return
    
    # Ensure new data directory exists
    new_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy old database to new location
    shutil.copy2(old_db_path, new_db_path)
    
    # Update schema if needed
    try:
        with sqlite3.connect(new_db_path) as conn:
            cursor = conn.cursor()
            
            # Check if metadata column exists
            cursor.execute("PRAGMA table_info(calls)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'metadata' not in columns:
                print("  📝 Adding metadata column...")
                cursor.execute("ALTER TABLE calls ADD COLUMN metadata TEXT DEFAULT '{}'")
            
            # Add indexes for better performance
            print("  📊 Adding database indexes...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_calls_caller_name ON calls(caller_name)")
            
            conn.commit()
            print("  ✅ Database schema updated successfully")
            
    except Exception as e:
        print(f"  ❌ Database migration failed: {e}")
        return False
    
    return True

def migrate_configuration():
    """Migrate configuration from v1 to v2"""
    print("⚙️ Migrating configuration...")
    
    # Read old config
    old_config = {}
    if Path("config.py").exists():
        try:
            with open("config.py", "r") as f:
                content = f.read()
                
            # Extract values using simple parsing
            for line in content.split('\n'):
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    old_config[key] = value
                    
        except Exception as e:
            print(f"  ⚠️  Could not read old config: {e}")
    
    # Create new .env file
    env_content = f"""# AI Calling System v2.0 Configuration
# Migrated from v1.0 on {datetime.now().isoformat()}

# Core Application Settings
SECRET_KEY={old_config.get('SECRET_KEY', 'your-super-secret-key-change-this-in-production')}
DEBUG=False
HOST=0.0.0.0
PORT=5000
ENVIRONMENT=production

# Synthflow API Configuration
SYNTHFLOW_API_KEY={old_config.get('SYNTHFLOW_API_KEY', '')}
SYNTHFLOW_BASE_URL=https://api.synthflow.ai/v2
SYNTHFLOW_TIMEOUT=30
SYNTHFLOW_RETRY_ATTEMPTS=3
SYNTHFLOW_ASSISTANT_ID={old_config.get('DEFAULT_ASSISTANT_ID', '')}
SYNTHFLOW_PHONE_NUMBER={old_config.get('SYNTHFLOW_PHONE_NUMBER', '')}

# Database Configuration
DATABASE_PATH=data/calls.db
DB_BACKUP_INTERVAL=3600
DB_MAX_CONNECTIONS=10
DB_TIMEOUT=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
STRUCTURED_LOGGING=true

# Security Settings
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
CORS_ORIGINS=*

# Performance Settings
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=false

# Feature Flags
ENABLE_CALL_SCHEDULING=true
ENABLE_BULK_OPERATIONS=true
ENABLE_ANALYTICS=true
ENABLE_WEBHOOKS=false

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("  ✅ Configuration migrated to .env file")
        
        # Validate critical settings
        missing = []
        if not old_config.get('SYNTHFLOW_API_KEY'):
            missing.append('SYNTHFLOW_API_KEY')
        if not old_config.get('DEFAULT_ASSISTANT_ID'):
            missing.append('SYNTHFLOW_ASSISTANT_ID')
        if not old_config.get('SYNTHFLOW_PHONE_NUMBER'):
            missing.append('SYNTHFLOW_PHONE_NUMBER')
        
        if missing:
            print(f"  ⚠️  Please update these values in .env: {', '.join(missing)}")
        
    except Exception as e:
        print(f"  ❌ Configuration migration failed: {e}")
        return False
    
    return True

def update_file_structure():
    """Update file structure for v2"""
    print("📁 Updating file structure...")
    
    # Create new directories
    directories = [
        "data",
        "logs", 
        "src",
        "src/api",
        "src/core", 
        "src/web",
        "src/utils",
        "src/config",
        "tests",
        "tests/unit",
        "tests/integration",
        "scripts"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created directory: {directory}")
    
    # Move old files if they exist
    moves = [
        ("templates", "templates"),  # Keep templates in root
        ("static", "static")         # Keep static in root
    ]
    
    for old_path, new_path in moves:
        if Path(old_path).exists() and old_path != new_path:
            if Path(new_path).exists():
                shutil.rmtree(new_path)
            shutil.move(old_path, new_path)
            print(f"  ✅ Moved {old_path} to {new_path}")
    
    return True

def cleanup_old_files():
    """Clean up old files that are no longer needed"""
    print("🧹 Cleaning up old files...")
    
    old_files = [
        "app_fixed.py",
        "debug_issues.py", 
        "debug_synthflow.py",
        "fix_phone_issue.py",
        "quick_api_test.py",
        "simple_api_test.py",
        "test_api.py",
        "test_complete_flow.py",
        "test_correct_api.py",
        "test_list_calls.py",
        "test_new_features.py",
        "test_real_call.py",
        "test_system.py",
        "test_web_api.py",
        "update_assistant.py"
    ]
    
    for file_path in old_files:
        if Path(file_path).exists():
            Path(file_path).unlink()
            print(f"  ✅ Removed old file: {file_path}")
    
    return True

def verify_migration():
    """Verify that migration was successful"""
    print("🔍 Verifying migration...")
    
    checks = [
        (".env", "Environment configuration"),
        ("data/calls.db", "Database"),
        ("src/", "Source code structure"),
        ("templates/", "Templates"),
        ("requirements-updated.txt", "Dependencies")
    ]
    
    all_good = True
    
    for path, description in checks:
        if Path(path).exists():
            print(f"  ✅ {description}: {path}")
        else:
            print(f"  ❌ Missing {description}: {path}")
            all_good = False
    
    return all_good

def main():
    """Run the complete migration process"""
    print("🚀 AI Calling System v1.0 → v2.0 Migration")
    print("=" * 50)
    
    try:
        # Step 1: Backup
        backup_dir = backup_existing_data()
        print(f"📦 Backup created at: {backup_dir}")
        
        # Step 2: Migrate database
        if not migrate_database():
            print("❌ Database migration failed")
            return 1
        
        # Step 3: Migrate configuration
        if not migrate_configuration():
            print("❌ Configuration migration failed")
            return 1
        
        # Step 4: Update file structure
        if not update_file_structure():
            print("❌ File structure update failed")
            return 1
        
        # Step 5: Clean up old files
        cleanup_old_files()
        
        # Step 6: Verify migration
        if not verify_migration():
            print("❌ Migration verification failed")
            return 1
        
        print("\n" + "=" * 50)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        
        print("\n📋 Next Steps:")
        print("1. Review and update .env file with your actual values")
        print("2. Install new dependencies: pip install -r requirements-updated.txt")
        print("3. Run tests: python -m pytest tests/")
        print("4. Start the application: python -m src.web.app")
        print("5. Check health: curl http://localhost:5000/health")
        
        print(f"\n💾 Backup available at: {backup_dir}")
        print("   Keep this backup until you've verified everything works correctly")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        print("Please check the backup and try again")
        return 1

if __name__ == "__main__":
    sys.exit(main())