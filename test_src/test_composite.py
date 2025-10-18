#!/usr/bin/env python3
import os
import sys
import django
import logging

# Add the project directory to Python path
sys.path.append('/home/ponir/Documents/clients/jake/ai-projects/stylerecomend/stylerecommend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stylerecommend.settings')
django.setup()

from imageprocessor.services import StyleRecommendationService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_composite_generation():
    print("=== Testing Composite Generation ===")
    
    try:
        service = StyleRecommendationService()
        result = service.generate_outfit_recommendations('casual', 'all', 2)
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
    test_composite_generation()
