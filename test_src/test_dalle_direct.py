#!/usr/bin/env python
"""
Test script to verify direct DALL-E 3 processing with uploaded image
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

def test_dalle_direct():
    print("🧪 Testing Direct DALL-E 3 Processing")
    print("=" * 45)
    
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
        test_image = Image.new('RGB', (300, 400), color='darkgreen')
        
        # Add some features to make it look like a shirt
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_image)
        
        # Draw a collar
        draw.rectangle([120, 50, 180, 80], fill='darkgreen', outline='black', width=2)
        
        # Draw buttons
        for i in range(5):
            y_pos = 100 + i * 40
            draw.ellipse([145, y_pos, 155, y_pos + 10], fill='black')
        
        # Save as temporary JPEG
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'JPEG')
            temp_jpg_path = tmp_file.name
        
        print(f"   ✅ Created test image: {temp_jpg_path}")
        
        # Test the service
        print("\n2. Testing direct DALL-E 3 processing...")
        processor = OpenAIImageProcessor()
        
        try:
            # Test the processing
            result = processor.process_image_with_openai(temp_jpg_path, 'shirt')
            
            if result['success']:
                print("   ✅ DALL-E 3 processing successful!")
                print(f"   📝 Method used: {result.get('method', 'unknown')}")
                print(f"   📋 Prompt used: {result.get('prompt_used', 'No prompt')}")
                
                # Save the processed image
                if result.get('processed_image_data'):
                    output_path = temp_jpg_path.replace('.jpg', '_processed.png')
                    with open(output_path, 'wb') as f:
                        f.write(result['processed_image_data'])
                    print(f"   💾 Processed image saved: {output_path}")
                    print("   🔍 Check the processed image to see the result!")
                
                # Show analysis
                analysis = result.get('analysis', '')
                if analysis:
                    print(f"\n   🔍 Processing info:")
                    print(f"      {analysis}")
                
            else:
                print(f"   ❌ DALL-E 3 processing failed: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Processing test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Clean up
        if os.path.exists(temp_jpg_path):
            os.remove(temp_jpg_path)
            print("\n   🧹 Cleaned up temporary test file")
        
        print("\n🎉 Direct DALL-E 3 processing test completed!")
        print("\n📋 How it works:")
        print("1. Takes your uploaded image")
        print("2. Sends your exact prompt directly to DALL-E 3")
        print("3. DALL-E 3 generates a processed image based on the prompt")
        print("4. The processed image is saved and displayed")
        print(f"\n💰 Cost: ~$0.04-0.08 per processed image")
        print("🎯 Prompt: 'Smooth out wrinkles and flatten the garment. Remove the background and place the garment on a pure white background. Make it look like a professional product photo. Maintain the natural shape of the clothing. only for [clothing_type] above.'")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_dalle_direct()
