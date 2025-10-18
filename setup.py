#!/usr/bin/env python
"""
Setup script for Style Recommend Django application
"""
import os
import sys
import subprocess

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    print("🚀 Setting up Style Recommend Django Application")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found. Please run this script from the Django project directory.")
        sys.exit(1)
    
    # Check if virtual environment exists
    if not os.path.exists('../env'):
        print("📦 Creating virtual environment...")
        success, output = run_command('cd .. && python -m venv env')
        if not success:
            print(f"❌ Failed to create virtual environment: {output}")
            sys.exit(1)
        print("✅ Virtual environment created")
    
    # Install requirements
    print("📥 Installing requirements...")
    success, output = run_command('source ../env/bin/activate && pip install -r requirements.txt')
    if not success:
        print(f"❌ Failed to install requirements: {output}")
        sys.exit(1)
    print("✅ Requirements installed")
    
    # Run migrations
    print("🗄️ Running database migrations...")
    success, output = run_command('source ../env/bin/activate && python manage.py migrate')
    if not success:
        print(f"❌ Failed to run migrations: {output}")
        sys.exit(1)
    print("✅ Database migrations completed")
    
    # Check for OpenAI API key
    print("🔑 Checking OpenAI API key...")
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set!")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY=your_api_key_here")
        print("   Or create a .env file with: OPENAI_API_KEY=your_api_key_here")
    else:
        print("✅ OpenAI API key found")
    
    # Create media directories
    print("📁 Creating media directories...")
    os.makedirs('media/original_images', exist_ok=True)
    os.makedirs('media/processed_images', exist_ok=True)
    print("✅ Media directories created")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Set your OpenAI API key (if not already set)")
    print("2. Run: source ../env/bin/activate && python manage.py runserver")
    print("3. Open: http://127.0.0.1:8000/")
    print("4. Upload and process your clothing images!")
    
    print("\n📚 For more information, see README.md")

if __name__ == '__main__':
    main()
