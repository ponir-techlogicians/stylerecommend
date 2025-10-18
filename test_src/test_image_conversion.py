#!/usr/bin/env python
"""
Test script to verify image conversion for OpenAI API compatibility
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

def test_image_conversion():
    print("🧪 Testing Image Conversion for OpenAI API")
    print("=" * 50)
    
    try:
        from imageprocessor.services import OpenAIImageProcessor
        from PIL import Image
        import tempfile
        
        # Create a test RGB image
        print("1. Creating test RGB image...")
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # Save as temporary JPEG
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'JPEG')
            temp_jpg_path = tmp_file.name
        
        print(f"   ✅ Created test JPEG: {temp_jpg_path}")
        
        # Test the conversion
        print("\n2. Testing image conversion...")
        processor = OpenAIImageProcessor()
        
        try:
            png_path = processor.convert_to_png(temp_jpg_path)
            print(f"   ✅ Converted to PNG: {png_path}")
            
            # Verify the converted image
            with Image.open(png_path) as converted_img:
                print(f"   📊 Original mode: RGB")
                print(f"   📊 Converted mode: {converted_img.mode}")
                print(f"   📊 Converted size: {converted_img.size}")
                
                if converted_img.mode in ['RGBA', 'LA', 'L']:
                    print("   ✅ Image format is compatible with OpenAI API!")
                else:
                    print(f"   ❌ Image format {converted_img.mode} is NOT compatible with OpenAI API")
            
            # Clean up
            if os.path.exists(png_path):
                os.remove(png_path)
                print("   🧹 Cleaned up temporary PNG file")
                
        except Exception as e:
            print(f"   ❌ Conversion failed: {e}")
        
        # Clean up
        if os.path.exists(temp_jpg_path):
            os.remove(temp_jpg_path)
            print("   🧹 Cleaned up temporary JPEG file")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_image_conversion()
