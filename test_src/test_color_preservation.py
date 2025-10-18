#!/usr/bin/env python
"""
Test script to verify color preservation in image processing
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

def test_color_preservation():
    print("🧪 Testing Color Preservation in Image Processing")
    print("=" * 55)
    
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
        
        # Create a test image with specific colors
        print("\n1. Creating test image with specific colors...")
        
        # Create a colored shirt image
        test_image = Image.new('RGB', (300, 400), color='darkgreen')  # Dark green shirt
        
        # Add some simple features to make it look like a shirt
        from PIL import ImageDraw
        draw = ImageDraw.Draw(test_image)
        
        # Draw a simple collar
        draw.rectangle([120, 50, 180, 80], fill='darkgreen', outline='black', width=2)
        
        # Draw buttons
        for i in range(5):
            y_pos = 100 + i * 40
            draw.ellipse([145, y_pos, 155, y_pos + 10], fill='black')
        
        # Save as temporary JPEG
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'JPEG')
            temp_jpg_path = tmp_file.name
        
        print(f"   ✅ Created dark green shirt test image: {temp_jpg_path}")
        
        # Test the service
        print("\n2. Testing image processing with color preservation...")
        processor = OpenAIImageProcessor()
        
        try:
            # Test the processing
            result = processor.process_image_with_openai(temp_jpg_path, 'shirt')
            
            if result['success']:
                print("   ✅ Image processing successful!")
                print(f"   📝 Method used: {result.get('method', 'unknown')}")
                print(f"   🔍 Analysis: {result.get('analysis', 'No analysis available')[:100]}...")
                
                # Save the result for inspection
                output_path = temp_jpg_path.replace('.jpg', '_processed.png')
                with open(output_path, 'wb') as f:
                    f.write(result['processed_image_data'])
                
                print(f"   💾 Processed image saved: {output_path}")
                print("   🔍 Please check if the colors are preserved in the processed image")
                
            else:
                print(f"   ❌ Image processing failed: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Processing test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Clean up
        if os.path.exists(temp_jpg_path):
            os.remove(temp_jpg_path)
            print("\n   🧹 Cleaned up temporary test file")
        
        print("\n🎉 Color preservation test completed!")
        print("\n📋 Summary:")
        print("- The system now tries multiple approaches:")
        print("  1. Original image editing API (best for color preservation)")
        print("  2. DALL-E 3 with improved prompts (if editing fails)")
        print("  3. Traditional processing (as final fallback)")
        print("- Check the processed image to verify color preservation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_color_preservation()
