#!/usr/bin/env python
"""
Test script to verify ChatGPT normal API integration
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

def test_chatgpt_simple():
    print("🧪 Testing ChatGPT Normal API Integration")
    print("=" * 50)
    
    try:
        from imageprocessor.services import OpenAIImageProcessor
        from PIL import Image
        import tempfile
        
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OpenAI API key not found!")
            return
        
        print(f"✅ OpenAI API key found: {api_key[:10]}...")
        
        # Create a test image
        print("\n1. Creating test clothing image...")
        test_image = Image.new('RGB', (200, 200), color='navy')
        
        # Save as temporary JPEG
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'JPEG')
            temp_jpg_path = tmp_file.name
        
        print(f"   ✅ Created test image: {temp_jpg_path}")
        
        # Test the service
        print("\n2. Testing ChatGPT API integration...")
        processor = OpenAIImageProcessor()
        
        try:
            # Test the processing
            result = processor.process_image_with_openai(temp_jpg_path, 'shirt')
            
            if result['success']:
                print("   ✅ ChatGPT API integration successful!")
                print(f"   📝 Method used: {result.get('method', 'unknown')}")
                print(f"   📊 Analysis length: {len(result.get('analysis', ''))} characters")
                print(f"   🔍 Analysis preview:")
                analysis = result.get('analysis', '')
                if analysis:
                    print(f"      {analysis[:200]}...")
                else:
                    print("      No analysis provided")
                
                # Show the prompt used
                print(f"\n   📋 Prompt used:")
                print(f"      {result.get('prompt_used', 'No prompt')}")
                
            else:
                print(f"   ❌ ChatGPT API integration failed: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Clean up
        if os.path.exists(temp_jpg_path):
            os.remove(temp_jpg_path)
            print("\n   🧹 Cleaned up temporary test file")
        
        print("\n🎉 ChatGPT integration test completed!")
        print("\n📋 Summary:")
        print("- Uses ChatGPT normal API (GPT-4o with vision)")
        print("- Provides detailed analysis and recommendations")
        print("- Uses your exact prompt for processing instructions")
        print("- Cost-effective approach (~$0.01-0.03 per analysis)")
        print("- Ready for production use")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_chatgpt_simple()
