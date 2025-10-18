#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/ponir/Documents/clients/jake/ai-projects/stylerecomend/stylerecommend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stylerecommend.settings')
django.setup()

from imageprocessor.services import StyleRecommendationService
from imageprocessor.models import WardrobeItem
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_outfit_generation():
    print("=== Testing Outfit Generation ===")
    
    # Check wardrobe items
    print(f"WardrobeItem count: {WardrobeItem.objects.count()}")
    
    # Get a sample item
    item = WardrobeItem.objects.first()
    if item:
        print(f"Sample item: {item.name}")
        print(f"Has processed_image: {hasattr(item, 'processed_image')}")
        if hasattr(item, 'processed_image') and item.processed_image:
            print(f"ProcessedImage: {item.processed_image}")
            print(f"Has processed_image field: {hasattr(item.processed_image, 'processed_image')}")
            print(f"Has original_image field: {hasattr(item.processed_image, 'original_image')}")
            if hasattr(item.processed_image, 'processed_image') and item.processed_image.processed_image:
                print(f"Processed image path: {item.processed_image.processed_image.path}")
                print(f"Processed image exists: {os.path.exists(item.processed_image.processed_image.path)}")
            if hasattr(item.processed_image, 'original_image') and item.processed_image.original_image:
                print(f"Original image path: {item.processed_image.original_image.path}")
                print(f"Original image exists: {os.path.exists(item.processed_image.original_image.path)}")
    
    # Test outfit generation
    print("\n=== Testing Outfit Generation ===")
    try:
        service = StyleRecommendationService()
        result = service.generate_outfit_recommendations('casual', 'all', 1)
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Outfits count: {len(result.get('outfits', []))}")
            print(f"Has composite image: {'composite_image_data' in result}")
            if 'composite_image_data' in result:
                print(f"Composite image size: {len(result['composite_image_data'])} bytes")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Exception during outfit generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_outfit_generation()
