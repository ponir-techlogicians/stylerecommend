#!/usr/bin/env python
"""
Script to help set up OpenAI API key and test the application
"""
import os
import sys

def main():
    print("🔑 OpenAI API Key Setup for Style Recommend")
    print("=" * 50)
    
    # Check if API key is already set
    current_key = os.getenv('OPENAI_API_KEY')
    if current_key:
        print(f"✅ OpenAI API key is already set: {current_key[:10]}...")
        print("You can now start the Django server!")
        return
    
    print("❌ OpenAI API key is not set.")
    print("\nTo set your API key, you have several options:")
    print("\n1. Set it temporarily for this session:")
    print("   export OPENAI_API_KEY=your_actual_api_key_here")
    print("   python manage.py runserver")
    
    print("\n2. Add it to your shell profile (permanent):")
    print("   echo 'export OPENAI_API_KEY=your_actual_api_key_here' >> ~/.bashrc")
    print("   source ~/.bashrc")
    
    print("\n3. Create a .env file in this directory:")
    print("   echo 'OPENAI_API_KEY=your_actual_api_key_here' > .env")
    print("   Then install python-dotenv and modify settings.py")
    
    print("\n4. Set it when running the server:")
    print("   OPENAI_API_KEY=your_actual_api_key_here python manage.py runserver")
    
    print("\n📝 To get an OpenAI API key:")
    print("1. Go to https://platform.openai.com/api-keys")
    print("2. Sign up or log in to your OpenAI account")
    print("3. Click 'Create new secret key'")
    print("4. Copy the key and use it in one of the methods above")
    
    print("\n⚠️  Important:")
    print("- Keep your API key secure and never commit it to version control")
    print("- You'll need credits in your OpenAI account to process images")
    print("- Each image processing request costs a small amount (usually $0.02-0.10)")

if __name__ == '__main__':
    main()
