# Style Recommend - AI Image Processor

A Django web application that uses OpenAI's API to process clothing images and transform them into professional product photos.

## Features

- Upload clothing images (jackets, shirts, pants, dresses, sweaters, hoodies, coats, blouses, skirts, shorts, and more!)
- AI-powered image processing using OpenAI API with customized prompts for each clothing type
- Automatic background removal and white background replacement
- Wrinkle smoothing and garment flattening
- Professional product photo styling optimized for each garment type
- Image gallery to view all processed images
- Real-time processing status updates
- Download processed images

## Prerequisites

- Python 3.8+
- OpenAI API key
- Django 5.2+

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd stylerecommend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root with your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   Or set it as an environment variable:
   ```bash
   export OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

8. **Access the application:**
   - Main application: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Usage

### Upload and Process Images

1. Go to the main page (http://127.0.0.1:8000/)
2. Select the clothing type (jacket, shirt, pants, dress, sweater, hoodie, coat, blouse, skirt, shorts, or other)
3. Upload an image file (JPG, PNG, GIF, BMP, WebP - max 10MB)
4. Click "Process Image"
5. Wait for the AI processing to complete
6. View the before/after comparison
7. Download the processed image

### View Gallery

- Navigate to the Gallery to see all processed images
- Click on any image to view detailed information
- Download processed images directly from the gallery

### Admin Panel

- Access the Django admin panel to manage all uploaded images
- View processing status, error messages, and detailed information
- Monitor processing times and OpenAI response IDs

## API Endpoints

- `GET /` - Upload form
- `POST /` - Upload and process image
- `GET /result/<image_id>/` - View processing result
- `GET /gallery/` - Image gallery
- `GET /detail/<image_id>/` - Detailed image view
- `GET /api/status/<image_id>/` - Check processing status (JSON)

## Image Processing Details

The application uses a two-step process with OpenAI's APIs:

### **Step 1: GPT-4 Vision Analysis**
Analyzes the uploaded clothing image to understand:
- Current condition (wrinkles, folds, positioning)
- Key features and design elements
- Optimal positioning for professional presentation
- Specific styling recommendations

### **Step 2: DALL-E 3 Generation**
Creates a new professional product photo based on the analysis with:
- Smooth, wrinkle-free appearance
- Pure white background
- Professional product photo styling
- Maintained natural clothing shape
- High-quality commercial photography style

### **Clothing Type Optimizations**
Each clothing type gets specialized analysis and generation prompts:

- **Jackets**: Focus on structure and clean lines
- **Shirts**: Clean collar and sleeve positioning  
- **Pants**: Clear waistband and leg positioning
- **Dresses**: Show silhouette and design details
- **Sweaters**: Display knit texture and design
- **Hoodies**: Show hood and pocket details
- **Coats**: Highlight length, collar, and closure
- **Blouses**: Show collar, sleeves, and decorative elements
- **Skirts**: Display shape, length, and design features
- **Shorts**: Show waistband and leg openings
- **Other**: Showcase best features and design details

### **Cost Considerations**
- **GPT-4 Vision**: ~$0.01-0.03 per image analysis
- **DALL-E 3**: ~$0.04-0.08 per image generation (HD quality)
- **Total**: ~$0.05-0.11 per processed image

## File Structure

```
stylerecommend/
├── imageprocessor/           # Main Django app
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── services.py          # OpenAI API service
│   ├── admin.py             # Admin configuration
│   ├── urls.py              # URL patterns
│   └── templates/           # HTML templates
├── stylerecommend/          # Django project settings
│   ├── settings.py          # Project settings
│   └── urls.py              # Main URL configuration
├── media/                   # User uploaded files
│   ├── original_images/     # Original uploaded images
│   └── processed_images/    # AI processed images
└── requirements.txt         # Python dependencies
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `DEBUG` - Django debug mode (default: True)
- `SECRET_KEY` - Django secret key (default: development key)

### Settings

Key settings in `settings.py`:
- Media files are served from `/media/` directory
- Maximum file size: 10MB
- Supported formats: JPG, PNG, GIF, BMP, WebP
- SQLite database (can be changed to PostgreSQL/MySQL for production)

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'openai'"**
   - Run: `pip install openai`

2. **"OpenAI API key not found"**
   - Set your OpenAI API key as an environment variable or in a `.env` file

3. **"Image processing failed"**
   - Check your OpenAI API key and account balance
   - Ensure the image file is valid and under 10MB
   - Check the error message in the admin panel

4. **"Permission denied" on media files**
   - Ensure the media directory has proper write permissions
   - Run: `chmod 755 media/` and `chmod 755 media/original_images/` and `chmod 755 media/processed_images/`

### Development Notes

- The application uses synchronous processing for simplicity
- For production, consider using Celery for asynchronous task processing
- Implement proper error handling and retry mechanisms
- Add rate limiting for API calls
- Consider implementing user authentication

## License

This project is for demonstration purposes. Please ensure you comply with OpenAI's usage policies and terms of service.

## Support

For issues or questions:
1. Check the Django admin panel for error messages
2. Review the console output for detailed error logs
3. Ensure all dependencies are properly installed
4. Verify your OpenAI API key is valid and has sufficient credits
