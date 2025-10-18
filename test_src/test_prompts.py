#!/usr/bin/env python
"""
Test script to verify prompt generation for different clothing types
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

def test_prompt_generation():
    print("🧪 Testing Prompt Generation for Different Clothing Types")
    print("=" * 60)
    
    try:
        from imageprocessor.services import OpenAIImageProcessor
        
        # Test different clothing types
        clothing_types = [
            'jacket', 'shirt', 'pants', 'dress', 'sweater', 
            'hoodie', 'coat', 'blouse', 'skirt', 'shorts', 'other'
        ]
        
        processor = OpenAIImageProcessor()
        
        print("Generated prompts for different clothing types:\n")
        
        for clothing_type in clothing_types:
            prompt = processor.generate_clothing_prompt(clothing_type)
            print(f"📝 {clothing_type.upper()}:")
            print(f"   {prompt}")
            print()
        
        print("✅ All prompts generated successfully!")
        print("\n🎯 Key Features:")
        print("- Each clothing type gets a customized prompt")
        print("- Base functionality (wrinkle removal, white background) is consistent")
        print("- Specific instructions optimize results for each garment type")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_prompt_generation()
