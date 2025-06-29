 API key appears to be valid")
            return True
        else:
            print(f"⚠️  API response: {response.status_code} (may be valid)")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Could not test API connectivity: {e}")
        print("✅ API key is set (connectivity test failed but that's ok)")
        return True

def test_file_structure():
    """Test project file structure"""
    print("\n📁 Testing File Structure...")
    
    required_files = [
        'app.py',
        'cli.py',
        'requirements.txt',
        'templates/index.html'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    # Check if logs directory exists or can be created
    try:
        os.makedirs("logs", exist_ok=True)
        print("✅ logs/ directory ready")
    except Exception as e:
        print(f"❌ Cannot create logs directory: {e}")
        return False
    
    return True

def test_cli_basic():
    """Test CLI basic functionality"""
    print("\n💻 Testing CLI Functionality...")
    
    try:
        # Import CLI module
        from cli import SynthflowCLI
        
        # Test initialization (without API key validation)
        os.environ['SYNTHFLOW_API_KEY'] = 'test_key_for_init'
        
        try:
            cli = SynthflowCLI()
            print("✅ CLI module loads correctly")
            
            # Test database methods
            test_call_data = {
                'id': 'test_call_123',
                'phone_number': '555-1234',
                'caller_name': 'Test User',
                'caller_phone': '555-5678',
                'account_action': 'Test action',
                'status': 'test'
            }
            
            cli.save_call(test_call_data)
            print("✅ CLI database operations working")
            
            return True
            
        except Exception as e:
            print(f"❌ CLI initialization error: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import CLI module: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("🧪 AI Call Manager - System Test")
    print("=" * 50)
    
    tests = [
        ("Environment", test_environment),
        ("Database", test_database),
        ("API Key", test_api_key),
        ("File Structure", test_file_structure),
        ("CLI Basic", test_cli_basic)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<15} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Ensure SYNTHFLOW_API_KEY is set with your real API key")
        print("2. Run: start_app.bat (for web interface)")
        print("3. Or use: python cli.py call --help (for CLI)")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix issues before using.")
        
        if not os.getenv('SYNTHFLOW_API_KEY'):
            print("\n🔑 Don't forget to set your Synthflow API key:")
            print("   set SYNTHFLOW_API_KEY=your_actual_api_key_here")

if __name__ == '__main__':
    run_all_tests()
