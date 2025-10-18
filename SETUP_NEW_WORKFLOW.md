# New Workflow Setup Guide

## Overview
The image processing workflow has been updated to use:
1. **ChatGPT API** for analyzing clothing images and extracting structured data
2. **Google Gemini API** for image processing (replacing DALL-E)

## Required API Keys

### 1. OpenAI API Key (for ChatGPT analysis)
- Get your API key from: https://platform.openai.com/api-keys
- Set the environment variable: `OPENAI_API_KEY=your_api_key_here`

### 2. Google Gemini API Key (for image processing)
- Get your API key from: https://makersuite.google.com/app/apikey
- Set the environment variable: `GEMINI_API_KEY=your_api_key_here`

## Environment Setup

Create a `.env` file in the project root with:
```bash
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## New Workflow

### 1. Image Upload
When an image is uploaded, the system now:
- Analyzes the image using ChatGPT to extract structured JSON data
- Processes the image using Gemini API for professional product photo styling
- Automatically creates a wardrobe item with AI-extracted attributes

### 2. ChatGPT Analysis
The ChatGPT analysis returns JSON with:
```json
{
    "type": "top/bottom/shoes/watch/accessories",
    "color": "primary color name",
    "style": "style description (e.g., casual, formal, sporty)",
    "material": "material/fabric type",
    "pattern": "pattern description or 'solid'",
    "occasion": "suitable occasion (casual, formal, business, party, sport, evening)",
    "season": "suitable season (spring, summer, fall, winter, all)"
}
```

### 3. Gemini Image Processing
The Gemini API processes the image to:
- Smooth out wrinkles and flatten the garment
- Remove the background and place on pure white background
- Make it look like a professional product photo
- Maintain the natural shape of the clothing

## Testing

Run the test script to verify the new workflow:
```bash
python test_new_workflow.py
```

## Dependencies

The following new dependencies have been added:
- `google-generativeai==0.8.3`
- `python-dotenv==1.0.0`

Install them with:
```bash
pip install -r requirements.txt
```

## Changes Made

### Services (`imageprocessor/services.py`)
- Added `GeminiImageProcessor` class
- Updated `OpenAIImageProcessor.analyze_clothing_image()` to return structured JSON
- Removed all DALL-E related methods

### Views (`imageprocessor/views.py`)
- Updated `process_image_async()` to use Gemini instead of DALL-E
- Updated `create_wardrobe_item_automatically()` to use ChatGPT analysis data
- Added fallback method for wardrobe item creation

### Requirements (`requirements.txt`)
- Added Google Gemini API dependency
- Added python-dotenv dependency

## Benefits

1. **More Accurate Analysis**: ChatGPT provides structured, detailed analysis of clothing items
2. **Better Image Processing**: Gemini API offers superior image editing capabilities
3. **Automatic Wardrobe Creation**: AI-extracted attributes automatically populate wardrobe items
4. **Cost Effective**: Gemini API may be more cost-effective than DALL-E for image processing
5. **Structured Data**: JSON format ensures consistent data extraction and storage

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure both API keys are set in environment variables
2. **Image Processing Failures**: Check Gemini API quota and rate limits
3. **Analysis Failures**: Verify OpenAI API key has sufficient credits
4. **JSON Parsing Errors**: The system includes fallback values for parsing failures

### Error Handling

The system includes comprehensive error handling:
- Fallback wardrobe item creation if AI analysis fails
- Graceful degradation if APIs are unavailable
- Detailed logging for debugging issues
