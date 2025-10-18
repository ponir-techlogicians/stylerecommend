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

def save_composite_image():
    print("=== Generating and Saving Composite Image ===")
    
    try:
        service = StyleRecommendationService()
        result = service.generate_outfit_recommendations('casual', 'all', 2)
        
        if result['success'] and 'composite_image_data' in result:
            # Save the composite image to a file
            with open('composite_test.png', 'wb') as f:
                f.write(result['composite_image_data'])
            print(f"Composite image saved as 'composite_test.png' ({len(result['composite_image_data'])} bytes)")
        else:
            print(f"Failed to generate composite: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    save_composite_image()
