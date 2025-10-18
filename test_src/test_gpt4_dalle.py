#!/usr/bin/env python
"""
Test script to verify GPT-4 Vision + DALL-E 3 integration
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

def test_gpt4_dalle_integration():
    print("🧪 Testing GPT-4 Vision + DALL-E 3 Integration")
    print("=" * 55)
    
    try:
        from imageprocessor.services import OpenAIImageProcessor
        from PIL import Image
        import tempfile
        
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OpenAI API key not found!")
            print("💡 Please set your API key: export OPENAI_API_KEY=your_key_here")
            return
        
        print(f"✅ OpenAI API key found: {api_key[:10]}...")
        
        # Create a test RGB image
        print("\n1. Creating test clothing image...")
        test_image = Image.new('RGB', (200, 200), color='navy')
        
        # Save as temporary JPEG
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'JPEG')
            temp_jpg_path = tmp_file.name
        
        print(f"   ✅ Created test image: {temp_jpg_path}")
        
        # Test the service
        print("\n2. Testing GPT-4 Vision + DALL-E 3 integration...")
        processor = OpenAIImageProcessor()
        
        try:
            # Test GPT-4 Vision analysis only (to avoid DALL-E costs)
            print("   🔍 Testing GPT-4 Vision analysis...")
            analysis_result = processor.analyze_image_with_gpt4_vision(temp_jpg_path, 'jacket')
            
            if analysis_result['success']:
                print("   ✅ GPT-4 Vision analysis successful!")
                print(f"   📝 Analysis preview: {analysis_result['analysis'][:150]}...")
                
                # Test DALL-E 3 generation (commented out to avoid costs)
                print("\n   🎨 DALL-E 3 generation test (skipped to avoid costs)")
                print("   💡 To test DALL-E 3, uncomment the generation test in the code")
                
                # Uncomment the following lines to test DALL-E 3 (will incur costs):
                # print("   🎨 Testing DALL-E 3 generation...")
                # generation_result = processor.generate_image_with_dalle3('jacket', analysis_result['analysis'])
                # if generation_result['success']:
                #     print("   ✅ DALL-E 3 generation successful!")
                # else:
                #     print(f"   ❌ DALL-E 3 generation failed: {generation_result['error']}")
                
            else:
                print(f"   ❌ GPT-4 Vision analysis failed: {analysis_result['error']}")
                
        except Exception as e:
            print(f"   ❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Clean up
        if os.path.exists(temp_jpg_path):
            os.remove(temp_jpg_path)
            print("\n   🧹 Cleaned up temporary test file")
            
        print("\n🎉 Integration test completed!")
        print("\n📋 Summary:")
        print("- GPT-4 Vision: Analyzes clothing images intelligently")
        print("- DALL-E 3: Generates professional product photos")
        print("- Combined approach: More reliable than image editing API")
        print("- Cost: Higher than image editing, but better results")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_gpt4_dalle_integration()
