#!/usr/bin/env python
"""
Test script to verify the Django application setup
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stylerecommend.settings')
django.setup()

def test_setup():
    print("🧪 Testing Style Recommend Django Application Setup")
    print("=" * 55)
    
    # Test 1: Check Django setup
    print("1. Testing Django setup...")
    try:
        from django.conf import settings
        print("   ✅ Django settings loaded successfully")
        print(f"   📁 Project directory: {settings.BASE_DIR}")
        print(f"   🗄️ Database: {settings.DATABASES['default']['ENGINE']}")
    except Exception as e:
        print(f"   ❌ Django setup failed: {e}")
        return False
    
    # Test 2: Check models
    print("\n2. Testing models...")
    try:
        from imageprocessor.models import ProcessedImage
        print("   ✅ ProcessedImage model imported successfully")
        print(f"   📊 Total images in database: {ProcessedImage.objects.count()}")
    except Exception as e:
        print(f"   ❌ Model test failed: {e}")
        return False
    
    # Test 3: Check OpenAI API key
    print("\n3. Testing OpenAI API key...")
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"   ✅ OpenAI API key found: {api_key[:10]}...")
    else:
        print("   ❌ OpenAI API key not set")
        print("   💡 Run: export OPENAI_API_KEY=your_key_here")
        print("   💡 Or run: python setup_api_key.py for instructions")
    
    # Test 4: Check services
    print("\n4. Testing services...")
    try:
        from imageprocessor.services import ImageValidationService
        print("   ✅ ImageValidationService imported successfully")
        
        # Test OpenAI service (will fail if no API key, but that's expected)
        try:
            from imageprocessor.services import OpenAIImageProcessor
            processor = OpenAIImageProcessor()
            print("   ✅ OpenAIImageProcessor initialized successfully")
        except ValueError as e:
            print(f"   ⚠️ OpenAIImageProcessor needs API key: {e}")
    except Exception as e:
        print(f"   ❌ Services test failed: {e}")
        return False
    
    # Test 5: Check media directories
    print("\n5. Testing media directories...")
    media_dirs = ['media', 'media/original_images', 'media/processed_images']
    for dir_path in media_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path} exists")
        else:
            print(f"   ❌ {dir_path} missing")
            os.makedirs(dir_path, exist_ok=True)
            print(f"   🔧 Created {dir_path}")
    
    # Test 6: Check templates
    print("\n6. Testing templates...")
    template_dirs = [
        'imageprocessor/templates',
        'imageprocessor/templates/imageprocessor'
    ]
    for dir_path in template_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path} exists")
        else:
            print(f"   ❌ {dir_path} missing")
            return False
    
    print("\n🎉 Setup test completed!")
    
    if api_key:
        print("\n✅ Everything looks good! You can start the server:")
        print("   python manage.py runserver")
        print("   Then visit: http://127.0.0.1:8000/")
    else:
        print("\n⚠️ Setup is mostly complete, but you need to set your OpenAI API key:")
        print("   export OPENAI_API_KEY=your_key_here")
        print("   python manage.py runserver")
    
    return True

if __name__ == '__main__':
    test_setup()
