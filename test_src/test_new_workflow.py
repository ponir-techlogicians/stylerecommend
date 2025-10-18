#!/usr/bin/env python
"""
Test script to verify the new ChatGPT + Gemini workflow
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

def test_new_workflow():
    print("🧪 Testing New ChatGPT + Gemini Workflow")
    print("=" * 50)
    
    try:
        from imageprocessor.services import OpenAIImageProcessor, GeminiImageProcessor
        from PIL import Image
        import tempfile
        
        # Check API keys
        openai_key = os.getenv('OPENAI_API_KEY')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not openai_key:
            print("❌ OpenAI API key not found!")
            return
        if not gemini_key:
            print("❌ Gemini API key not found!")
            return
        
        print(f"✅ OpenAI API key found: {openai_key[:10]}...")
        print(f"✅ Gemini API key found: {gemini_key[:10]}...")
        
        # Create a test image
        print("\n1. Creating test clothing image...")
        test_image = Image.new('RGB', (300, 400), color='darkblue')
        
        # Add some features to make it look like a shirt
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_image)
        
        # Draw a collar
        draw.rectangle([120, 50, 180, 80], fill='darkblue', outline='black', width=2)
        
        # Draw buttons
        for i in range(5):
            y_pos = 100 + i * 40
            draw.ellipse([145, y_pos, 155, y_pos + 10], fill='black')
        
        # Save as temporary JPEG
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'JPEG')
            temp_jpg_path = tmp_file.name
        
        print(f"   ✅ Created test image: {temp_jpg_path}")
        
        # Test ChatGPT analysis
        print("\n2. Testing ChatGPT clothing analysis...")
        openai_processor = OpenAIImageProcessor()
        
        try:
            analysis_result = openai_processor.analyze_clothing_image(temp_jpg_path, 'shirt')
            
            if analysis_result['success']:
                analysis_data = analysis_result['analysis']
                print(f"   ✅ ChatGPT Analysis:")
                print(f"      Type: {analysis_data.get('type', 'N/A')}")
                print(f"      Color: {analysis_data.get('color', 'N/A')}")
                print(f"      Style: {analysis_data.get('style', 'N/A')}")
                print(f"      Material: {analysis_data.get('material', 'N/A')}")
                print(f"      Pattern: {analysis_data.get('pattern', 'N/A')}")
                print(f"      Occasion: {analysis_data.get('occasion', 'N/A')}")
                print(f"      Season: {analysis_data.get('season', 'N/A')}")
            else:
                print(f"   ❌ ChatGPT analysis failed: {analysis_result.get('error')}")
                return
                
        except Exception as e:
            print(f"   ❌ Error in ChatGPT analysis: {e}")
            return
        
        # Test Gemini image processing
        print("\n3. Testing Gemini image processing...")
        gemini_processor = GeminiImageProcessor()
        
        try:
            gemini_result = gemini_processor.process_image_with_gemini(temp_jpg_path, 'shirt')
            
            if gemini_result['success']:
                print(f"   ✅ Gemini processing successful")
                print(f"      Method: {gemini_result.get('method', 'N/A')}")
                print(f"      Response ID: {gemini_result.get('response_id', 'N/A')}")
                print(f"      Analysis: {gemini_result.get('analysis', 'N/A')}")
            else:
                print(f"   ❌ Gemini processing failed: {gemini_result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Error in Gemini processing: {e}")
        
        # Clean up
        try:
            os.remove(temp_jpg_path)
            print(f"\n   ✅ Cleaned up test image: {temp_jpg_path}")
        except Exception as e:
            print(f"\n   ⚠️  Could not remove test image: {e}")
        
        print("\n🎉 New workflow test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_workflow()
