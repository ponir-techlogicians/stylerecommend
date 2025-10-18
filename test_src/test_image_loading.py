#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/ponir/Documents/clients/jake/ai-projects/stylerecomend/stylerecommend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stylerecommend.settings')
django.setup()

from imageprocessor.models import WardrobeItem
from PIL import Image

def test_image_loading():
    print("=== Testing Image Loading ===")
    
    # Get a sample wardrobe item
    item = WardrobeItem.objects.first()
    if not item:
        print("No wardrobe items found!")
        return
    
    print(f"Testing item: {item.name}")
    print(f"Item type: {type(item)}")
    print(f"Has processed_image: {hasattr(item, 'processed_image')}")
    
    if hasattr(item, 'processed_image') and item.processed_image:
        print(f"ProcessedImage: {item.processed_image}")
        
        # Try to load processed image
        if hasattr(item.processed_image, 'processed_image') and item.processed_image.processed_image:
            try:
                image_path = item.processed_image.processed_image.path
                print(f"Processed image path: {image_path}")
                print(f"File exists: {os.path.exists(image_path)}")
                
                if os.path.exists(image_path):
                    img = Image.open(image_path)
                    print(f"Successfully loaded processed image: {img.size}")
                else:
                    print("Processed image file not found!")
            except Exception as e:
                print(f"Error loading processed image: {e}")
        
        # Try to load original image
        if hasattr(item.processed_image, 'original_image') and item.processed_image.original_image:
            try:
                image_path = item.processed_image.original_image.path
                print(f"Original image path: {image_path}")
                print(f"File exists: {os.path.exists(image_path)}")
                
                if os.path.exists(image_path):
                    img = Image.open(image_path)
                    print(f"Successfully loaded original image: {img.size}")
                else:
                    print("Original image file not found!")
            except Exception as e:
                print(f"Error loading original image: {e}")
    else:
        print("No processed_image found!")

if __name__ == "__main__":
    test_image_loading()
