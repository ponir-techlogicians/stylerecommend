import os
import base64
import requests
import tempfile
import json
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from openai import OpenAI
try:
    from google import genai
except ImportError:
    genai = None
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import logging
from .models import ProcessedImage, WardrobeItem, OutfitRecommendation, OutfitItem

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# Concurrent processing imports
import asyncio
import concurrent.futures
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class GeminiImageProcessor:
    """Service class for processing images with Google Gemini API"""
    
    def __init__(self):
        """Initialize Gemini client"""
        if genai is None:
            raise ValueError(
                "Google Gemini library not available. Please install google-generativeai package."
            )
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "Gemini API key not found. Please set the GEMINI_API_KEY environment variable."
            )
        self.client = genai.Client(api_key=api_key)
    
    def process_image_with_gemini(self, image_path, clothing_type):
        """Process image using Gemini API for professional product photo"""
        try:
            # Load the image
            image_to_edit = Image.open(image_path)
            
            # Define the editing prompt
            edit_prompt = (
                f"Only process the {clothing_type}. Ignore and do not alter any other "
                f"garments or regions such as pants, shoes, skin, hair, or props. "
                f"Isolate the {clothing_type}, remove its background, and place it on a "
                f"pure white background. Smooth out wrinkles and flatten the {clothing_type} "
                f"while keeping its natural shape. Center and crop the frame around only "
                f"the {clothing_type} to look like a professional product photo."
            )
            
            # Call the Gemini API
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[edit_prompt, image_to_edit]
            )

            # 1. Access the usage_metadata attribute
            usage = response.usage_metadata
            print("\n--- Token Usage Details ---")
            print(f"Input Prompt Token Count: {usage.prompt_token_count}")
            # Note: For multimodal calls (image + text), prompt_token_count includes both.
            # The image itself is tokenized at a fixed rate based on its size (e.g., 258 tokens for a small image, or 258 tokens per 768x768 tile).
            print(f"Output Token Count (Candidates): {usage.candidates_token_count}")
            print(f"Total Token Count: {usage.total_token_count}")
            print("---------------------------\n")
            
            # Process and save the edited image
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    edited_image = Image.open(BytesIO(part.inline_data.data))
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                        edited_image.save(tmp_file.name, 'PNG')
                        processed_path = tmp_file.name
                    
                    # Read the processed image data
                    with open(processed_path, 'rb') as f:
                        processed_data = f.read()
                    
                    # Clean up
                    os.remove(processed_path)
                    
                    return {
                        'success': True,
                        'processed_image_data': processed_data,
                        'response_id': 'gemini_processed',
                        'analysis': 'Processed using Gemini API for professional product photo',
                        'method': 'gemini'
                    }
            
            return {
                'success': False,
                'error': 'No processed image returned from Gemini API'
            }
            
        except Exception as e:
            logger.error(f"Error processing image with Gemini: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class OpenAIImageProcessor:
    """Service class for processing images with OpenAI API"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable. "
                "Run 'python setup_api_key.py' for setup instructions."
            )
        self.client = OpenAI(api_key=api_key)
    
    def generate_clothing_prompt(self, clothing_type):
        """Generate the appropriate prompt based on clothing type"""
        return f"Smooth out wrinkles and flatten the garment. Remove the background and place the garment on a pure white background. Make it look like a professional product photo. Maintain the natural shape of the clothing. only for {clothing_type} above."
    
    def encode_image_to_base64(self, image_path):
        """Encode image file to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            raise
    
    def convert_to_png(self, image_path):
        """Convert image to PNG format for OpenAI API compatibility"""
        from PIL import Image
        
        # Create a temporary PNG file
        png_path = image_path.rsplit('.', 1)[0] + '_temp.png'
        
        # Open the original image and convert to PNG
        with Image.open(image_path) as img:
            original_mode = img.mode
            logger.info(f"Original image mode: {original_mode}")
            
            # OpenAI requires RGBA, LA, or L format - convert to RGBA
            if img.mode == 'RGBA':
                # Already in RGBA format
                logger.info("Image already in RGBA format")
                pass
            elif img.mode == 'LA':
                # Already in LA format
                logger.info("Image already in LA format")
                pass
            elif img.mode == 'L':
                # Already in L format
                logger.info("Image already in L format")
                pass
            elif img.mode == 'P':
                # Palette mode - convert to RGBA to preserve transparency
                logger.info("Converting from P to RGBA")
                img = img.convert('RGBA')
            elif img.mode == 'RGB':
                # RGB mode - convert to RGBA (add alpha channel)
                logger.info("Converting from RGB to RGBA")
                img = img.convert('RGBA')
            elif img.mode in ('CMYK', 'YCbCr', 'HSV', 'LAB'):
                # Other modes - convert to RGBA
                logger.info(f"Converting from {img.mode} to RGBA")
                img = img.convert('RGBA')
            else:
                # Fallback - convert to RGBA
                logger.info(f"Converting from {img.mode} to RGBA (fallback)")
                img = img.convert('RGBA')
            
            logger.info(f"Final image mode: {img.mode}")
            
            # Save as PNG
            img.save(png_path, 'PNG')
            logger.info(f"Saved PNG file: {png_path}")
        
        return png_path

    def analyze_clothing_image(self, image_path, clothing_type):
        """Analyze the clothing image using ChatGPT and return structured JSON"""
        try:
            # Convert image to PNG format for better compatibility
            png_path = self.convert_to_png(image_path)
            
            # Encode the image to base64
            with open(png_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Generate the analysis prompt for structured JSON response
            desired_type_mapping = {
                'shirt': 'top', 'tshirt': 'top', 'sweater': 'top', 'hoodie': 'top', 'blouse': 'top', 'top': 'top',
                'jacket': 'outerwear', 'coat': 'outerwear', 'outerwear': 'outerwear',
                'pants': 'bottom', 'skirt': 'bottom', 'shorts': 'bottom', 'jeans': 'bottom', 'bottom': 'bottom',
                'dress': 'dress',
                'shoes': 'shoes', 'sneakers': 'shoes', 'heels': 'shoes', 'boots': 'shoes',
                'watch': 'accessories', 'belt': 'accessories', 'hat': 'accessories', 'bag': 'accessories', 'accessories': 'accessories'
            }
            desired_type = desired_type_mapping.get((clothing_type or '').lower(), 'accessories')

            analysis_prompt = f"""Analyze this image but focus EXCLUSIVELY on the {clothing_type}. 
Ignore all other garments, body parts, or background. If multiple garments are visible, consider only the {clothing_type}. 
Set the JSON field \"type\" to \"{desired_type}\" exactly.

Return a single JSON object:

{{
    \"type\": \"{desired_type}\",
    \"color\": \"primary color name\",
    \"style\": \"style description (e.g., casual, formal, sporty)\",
    \"material\": \"material/fabric type\",
    \"pattern\": \"pattern description or 'solid'\",
    \"occasion\": \"suitable occasion (casual, formal, business, party, sport, evening)\",
    \"season\": \"suitable season (spring, summer, fall, winter, all)\"
}}

Focus on accurately identifying FOR THE {clothing_type} ONLY:
1. The primary color and any patterns
2. The style and material
3. Suitable occasions and seasons

Return ONLY the JSON object, no additional text."""
            
            # Prepare the message for GPT-4 Vision
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            # Call GPT-4 Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.1
            )

            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            print(f"Prompt Tokens: {prompt_tokens}")
            print(f"Completion Tokens: {completion_tokens}")
            print(f"Total Tokens: {total_tokens}")
            
            if response.choices and len(response.choices) > 0:
                analysis_text = response.choices[0].message.content
                print(analysis_text)
                
                # Try to parse JSON response
                try:
                    # First, try direct JSON parsing
                    analysis_data = json.loads(analysis_text)

                    return {
                        'success': True,
                        'analysis': analysis_data,
                        'response_id': response.id
                    }
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code blocks
                    try:
                        # Look for JSON in markdown code blocks
                        import re
                        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', analysis_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                            analysis_data = json.loads(json_str)
                            return {
                                'success': True,
                                'analysis': analysis_data,
                                'response_id': response.id
                            }
                        
                        # Try to find JSON object without code blocks
                        json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            analysis_data = json.loads(json_str)
                            return {
                                'success': True,
                                'analysis': analysis_data,
                                'response_id': response.id
                            }
                    except (json.JSONDecodeError, AttributeError):
                        pass
                    
                    # Fallback: extract information from text or return default
                    logger.warning(f"Failed to parse JSON from ChatGPT response: {analysis_text}")
                    return {
                        'success': True,
                        'analysis': {
                            "type": clothing_type,
                            "color": "other",
                            "style": "casual",
                            "material": "unknown",
                            "pattern": "solid",
                            "occasion": "casual",
                            "season": "all"
                        },
                        'response_id': response.id,
                        'raw_text': analysis_text
                    }
            else:
                return {
                    'success': False,
                    'error': 'No analysis response from ChatGPT API'
                }
                
        except Exception as e:
            logger.error(f"Error analyzing clothing image: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # Clean up temporary PNG file
            if 'png_path' in locals() and os.path.exists(png_path):
                try:
                    os.remove(png_path)
                except Exception as e:
                    logger.warning(f"Could not remove temporary PNG file {png_path}: {e}")


    def process_image_with_traditional_method(self, image_path, clothing_type):
        """Process image using traditional image processing techniques"""
        try:
            from PIL import Image, ImageFilter, ImageEnhance
            import numpy as np
            
            # Open the original image
            with Image.open(image_path) as img:
                # Convert to RGBA for better processing
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Create a white background
                white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                
                # For now, just place the original image on white background
                # In a more sophisticated implementation, you'd use AI to detect and remove the original background
                processed_img = img
                
                # Save the processed image
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    processed_img.save(tmp_file.name, 'PNG')
                    processed_path = tmp_file.name
                
                # Read the processed image data
                with open(processed_path, 'rb') as f:
                    processed_data = f.read()
                
                # Clean up
                os.remove(processed_path)
                
                return {
                    'success': True,
                    'processed_image_data': processed_data,
                    'prompt_used': self.generate_clothing_prompt(clothing_type),
                    'response_id': 'traditional_processing',
                    'analysis': 'Processed using traditional image processing techniques',
                    'method': 'traditional'
                }
                
        except Exception as e:
            logger.error(f"Error in traditional processing: {e}")
            return {
                'success': False,
                'error': str(e)
            }




    
    def save_processed_image(self, processed_image_data, original_filename):
        """Save processed image data to a file"""
        try:
            # Create a filename for the processed image
            filename_parts = original_filename.rsplit('.', 1)
            if len(filename_parts) == 2:
                name, ext = filename_parts
                processed_filename = f"{name}_processed.{ext}"
            else:
                processed_filename = f"{original_filename}_processed.png"
            
            # Create Django ContentFile from the processed image data
            processed_file = ContentFile(processed_image_data, name=processed_filename)
            
            return processed_file
            
        except Exception as e:
            logger.error(f"Error saving processed image: {e}")
            raise


class NanobananaMannequinService:
    """Service for generating mannequin images using Nanobanana/Gemini API"""
    
    def __init__(self):
        """Initialize Gemini client for mannequin generation"""
        if genai is None:
            raise ValueError(
                "Google Gemini library not available. Please install google-generativeai package."
            )
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                "Gemini API key not found. Please set the GEMINI_API_KEY environment variable."
            )
        self.client = genai.Client(api_key=api_key)
    
    def generate_mannequin_image(self, composite_image_data, occasion='casual', season='all'):
        """Generate mannequin image from composite outfit image"""
        try:
            logger.info(f"Starting mannequin generation for {occasion} occasion in {season} season")
            
            # Convert bytes to PIL Image
            from PIL import Image
            from io import BytesIO
            
            composite_image = Image.open(BytesIO(composite_image_data))
            logger.info(f"Composite image loaded: {composite_image.size}, mode: {composite_image.mode}")
            
            # Create prompt based on occasion and season
            edit_prompt = f"""I have an outfit combination for a {occasion} occasion in {season} season. 
            Place the combination's clothes on a mannequin. 
            Remove the background and display the garments on a pure white backdrop. 
            Make it look professional and stylish for the {occasion} occasion."""
            
            logger.info("Calling Gemini API for mannequin generation...")
            
            # Call the Gemini API
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[edit_prompt, composite_image]
            )

            # 1. Access the usage_metadata attribute
            usage = response.usage_metadata

            # 2. Print the token details
            print("\n--- Token Usage Details ---")
            print(f"Input Prompt Token Count: {usage.prompt_token_count}")
            # Note: For multimodal calls (image + text), prompt_token_count includes both.
            # The image itself is tokenized at a fixed rate based on its size (e.g., 258 tokens for a small image, or 258 tokens per 768x768 tile).
            print(f"Output Token Count (Candidates): {usage.candidates_token_count}")
            print(f"Total Token Count: {usage.total_token_count}")
            print("---------------------------\n")
            
            logger.info(f"Gemini API response received: {len(response.candidates)} candidates")
            
            # Process the response
            for i, part in enumerate(response.candidates[0].content.parts):
                logger.info(f"Processing part {i}: inline_data present = {part.inline_data is not None}")
                if part.inline_data is not None:
                    mannequin_image = Image.open(BytesIO(part.inline_data.data))
                    logger.info(f"Mannequin image created: {mannequin_image.size}, mode: {mannequin_image.mode}")
                    
                    # Convert back to bytes
                    img_buffer = BytesIO()
                    mannequin_image.save(img_buffer, format='PNG')
                    mannequin_image_data = img_buffer.getvalue()
                    
                    logger.info(f"Mannequin image data size: {len(mannequin_image_data)} bytes")
                    
                    return {
                        'success': True,
                        'mannequin_image_data': mannequin_image_data,
                        'response_id': 'nanobanana_mannequin',
                        'analysis': f'Generated mannequin image for {occasion} occasion in {season} season',
                        'method': 'nanobanana'
                    }
            
            logger.warning("No mannequin image data found in response")
            return {
                'success': False,
                'error': 'No mannequin image returned from Nanobanana API'
            }
            
        except Exception as e:
            logger.error(f"Error generating mannequin image: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }


class OutfitAnalysis(BaseModel):
    """Pydantic model for individual outfit analysis output"""
    style_description: str = Field(description="Brief description of the outfit style")
    color_scheme: List[str] = Field(description="List of primary and secondary colors")
    style_tags: List[str] = Field(description="List of style tags (3-5 tags)")
    confidence_score: float = Field(description="Overall confidence score between 0 and 1")
    style_notes: str = Field(description="Detailed notes about the outfit including style cohesion, occasion appropriateness, season suitability, color harmony, material compatibility, and style consistency")
    improvement_suggestions: List[str] = Field(description="List of specific improvement suggestions based on the detailed item analysis")


class OutfitRanking(BaseModel):
    """Pydantic model for individual outfit ranking within batch analysis"""
    outfit_id: int = Field(description="Index/ID of the outfit in the batch")
    style_description: str = Field(description="Brief description of the outfit style")
    color_scheme: List[str] = Field(description="List of primary and secondary colors")
    style_tags: List[str] = Field(description="List of style tags (3-5 tags)")
    confidence_score: float = Field(description="Overall confidence score between 0 and 1")
    style_notes: str = Field(description="Detailed notes about the outfit")
    improvement_suggestions: List[str] = Field(description="List of specific improvement suggestions")
    ranking_position: int = Field(description="Position in the ranking (1 = best)")


class BatchOutfitAnalysis(BaseModel):
    """Pydantic model for batch outfit analysis output"""
    outfit_rankings: List[OutfitRanking] = Field(description="List of all outfits ranked from best to worst")
    overall_analysis: str = Field(description="Overall analysis of the outfit collection and trends")
    top_recommendations: List[int] = Field(description="List of outfit IDs that are the top recommendations")


class StyleRecommendationService:
    """Service for AI-powered style recommendations"""
    
    def __init__(self):
        """Initialize OpenAI client and LangChain components"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
            )
        self.client = OpenAI(api_key=api_key)
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=2000,  # Increased for batch analysis
            api_key=api_key
        )
        self.output_parser = PydanticOutputParser(pydantic_object=OutfitAnalysis)
        self.batch_output_parser = PydanticOutputParser(pydantic_object=BatchOutfitAnalysis)
    
    def analyze_wardrobe_item(self, wardrobe_item):
        """Analyze a wardrobe item and extract style information"""
        try:
            if not wardrobe_item.processed_image.processed_image:
                return {
                    'success': False,
                    'error': 'No processed image available for analysis'
                }
            
            # Get image path
            image_path = wardrobe_item.processed_image.processed_image.path
            
            # Convert to PNG for analysis
            processor = OpenAIImageProcessor()
            png_path = processor.convert_to_png(image_path)
            
            # Encode image to base64
            with open(png_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create analysis prompt
            analysis_prompt = f"""Analyze this {wardrobe_item.category} clothing item and provide detailed style information:

1. PRIMARY COLOR: Identify the exact primary color (black, white, navy, etc.)
2. SECONDARY COLORS: List any secondary colors or patterns
3. STYLE: Describe the style (casual, formal, sporty, elegant, etc.)
4. OCCASION: What occasions is this suitable for? (casual, formal, business, party, sport, evening, weekend, travel)
5. SEASON: What season(s) is this suitable for? (spring, summer, fall, winter, all)
6. MATERIAL: What material/fabric does this appear to be made of?
7. STYLE TAGS: Provide 3-5 style tags that describe this item (e.g., "minimalist", "vintage", "preppy", "edgy")
8. COLOR PALETTE: Extract the main colors in hex format if possible

Respond in JSON format:
{{
    "primary_color": "color_name",
    "secondary_colors": ["color1", "color2"],
    "style": "style_description",
    "suitable_occasions": ["occasion1", "occasion2"],
    "suitable_seasons": ["season1", "season2"],
    "material": "material_description",
    "style_tags": ["tag1", "tag2", "tag3"],
    "color_palette": ["#hex1", "#hex2"],
    "confidence": 0.85
}}"""
            
            # Call GPT-4 Vision API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=800,
                temperature=0.1
            )
            
            if response.choices and len(response.choices) > 0:
                analysis_text = response.choices[0].message.content
                
                # Try to parse JSON response
                try:
                    analysis_data = json.loads(analysis_text)
                    return {
                        'success': True,
                        'analysis': analysis_data,
                        'response_id': response.id
                    }
                except json.JSONDecodeError:
                    # Fallback: extract information from text
                    return {
                        'success': True,
                        'analysis': self._extract_analysis_from_text(analysis_text),
                        'response_id': response.id,
                        'raw_text': analysis_text
                    }
            else:
                return {
                    'success': False,
                    'error': 'No analysis response from GPT-4 Vision API'
                }
                
        except Exception as e:
            logger.error(f"Error analyzing wardrobe item: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # Clean up temporary PNG file
            if 'png_path' in locals() and os.path.exists(png_path):
                try:
                    os.remove(png_path)
                except Exception as e:
                    logger.warning(f"Could not remove temporary PNG file {png_path}: {e}")
    
    def _extract_analysis_from_text(self, text):
        """Extract analysis information from text when JSON parsing fails"""
        # Simple text extraction - in a real implementation, you'd use more sophisticated parsing
        return {
            "primary_color": "other",
            "secondary_colors": [],
            "style": "casual",
            "suitable_occasions": ["casual"],
            "suitable_seasons": ["all"],
            "material": "unknown",
            "style_tags": ["basic"],
            "color_palette": [],
            "confidence": 0.5,
            "raw_analysis": text
        }
    
    def generate_outfit_recommendations(self, user=None, occasion='casual', season='all', max_outfits=5):
        """Generate outfit recommendations from wardrobe items"""
        try:
            # Get available wardrobe items
            wardrobe_items = WardrobeItem.objects.all()
            if user is not None:
                wardrobe_items = wardrobe_items.filter(user=user)
            
            if not wardrobe_items.exists():
                return {
                    'success': False,
                    'error': 'No wardrobe items available for recommendations'
                }
            
            # Filter items by occasion and season with more precise matching
            # First try exact matches for occasion and season
            exact_matches = wardrobe_items.filter(
                Q(occasion=occasion) | Q(occasion='all'),
                Q(season=season) | Q(season='all')
            )
            
            logger.info(f"Filtering for occasion='{occasion}', season='{season}'")
            logger.info(f"Exact matches found: {exact_matches.count()}")
            
            # If we don't have enough items, be more flexible but still prioritize matches
            if exact_matches.count() >= 3:  # Need at least 3 items for good combinations
                filtered_items = exact_matches
                logger.info("Using exact matches for filtering")
            else:
                # Fallback: include items that are close matches
                if occasion == 'casual':
                    # For casual, include casual, business, and all items
                    filtered_items = wardrobe_items.filter(
                        Q(occasion__in=['casual', 'business', 'all']) | Q(occasion=''),
                        Q(season=season) | Q(season='all')
                    )
                else:
                    # For other occasions, be more inclusive but still prioritize the requested occasion
                    filtered_items = wardrobe_items.filter(
                        Q(occasion=occasion) | Q(occasion='casual') | Q(occasion='business') | Q(occasion='all') | Q(occasion=''),
                        Q(season=season) | Q(season='all')
                    )
                logger.info(f"Using fallback filtering, found {filtered_items.count()} items")
            
            # Log the selected items for debugging
            for item in filtered_items[:5]:  # Log first 5 items
                logger.info(f"Selected item: {item.name} - Occasion: {item.occasion}, Season: {item.season}")
            
            if not filtered_items.exists():
                return {
                    'success': False,
                    'error': f'No items suitable for {occasion} occasion and {season} season'
                }
            
            # Group items by category
            tops = filtered_items.filter(category='top')
            bottoms = filtered_items.filter(category='bottom')
            shoes = filtered_items.filter(category='shoes')
            accessories = filtered_items.filter(category='accessories')
            outerwear = filtered_items.filter(category='outerwear')
            dresses = filtered_items.filter(category='dress')
            
            # Create outfit combinations
            outfits = []
            
            # Generate dress outfits
            for dress in dresses:
                outfit_items = [dress]
                
                # Add shoes
                if shoes.exists():
                    outfit_items.append(shoes.first())
                
                # Add accessories
                if accessories.exists():
                    outfit_items.append(accessories.first())
                
                # Add outerwear if needed
                if outerwear.exists() and season in ['fall', 'winter']:
                    outfit_items.append(outerwear.first())
                
                outfits.append(self._create_outfit_from_items(
                    outfit_items, occasion, season, f"Elegant {dress.color} Dress"
                ))
            
            # Generate top + bottom outfits
            for top in tops:
                for bottom in bottoms:
                    outfit_items = [top, bottom]
                    
                    # Add shoes
                    if shoes.exists():
                        outfit_items.append(shoes.first())
                    
                    # Add accessories
                    if accessories.exists():
                        outfit_items.append(accessories.first())
                    
                    # Add outerwear if needed
                    if outerwear.exists() and season in ['fall', 'winter']:
                        outfit_items.append(outerwear.first())
                    
                    outfit_name = f"{top.color.title()} {top.category.title()} & {bottom.color.title()} {bottom.category.title()}"
                    outfits.append(self._create_outfit_from_items(
                        outfit_items, occasion, season, outfit_name
                    ))
            
            # Generate single-item outfits if no combinations are possible
            if not outfits:
                # Create outfits with individual items
                for item in filtered_items:
                    outfit_items = [item]
                    
                    # Add shoes if available and not already a shoe
                    if shoes.exists() and item.category != 'shoes':
                        outfit_items.append(shoes.first())
                    
                    # Add accessories if available and not already an accessory
                    if accessories.exists() and item.category != 'accessories':
                        outfit_items.append(accessories.first())
                    
                    outfit_name = f"Stylish {item.color.title()} {item.category.title()}"
                    outfits.append(self._create_outfit_from_items(
                        outfit_items, occasion, season, outfit_name
                    ))


            # Use AI to analyze and rank ALL outfits in a single batch
            batch_analysis = self._analyze_all_outfits_with_ai(outfits, occasion, season, max_outfits)
            ai_outfits = batch_analysis['outfits']
            
            # Generate individual flat-lay and mannequin images for each outfit concurrently
            ai_outfits = self._process_outfits_concurrently(ai_outfits, occasion, season)
            
            result_data = {
                'success': True,
                'outfits': ai_outfits,
                'total_combinations': len(outfits),
                'total_analyzed': batch_analysis['total_analyzed'],
                'overall_analysis': batch_analysis['overall_analysis']
            }
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error generating outfit recommendations: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_individual_outfit_images(self, occasion='casual', season='all', max_outfits=5):
        """Generate individual flat-lay images for each outfit combination"""
        try:
            # Get outfit recommendations
            recommendations = self.generate_outfit_recommendations(occasion, season, max_outfits)
            
            if not recommendations['success']:
                return recommendations
            
            outfits = recommendations['outfits']
            
            if not outfits:
                return {
                    'success': False,
                    'error': 'No outfits generated'
                }
            
            # Generate individual flat-lay images
            image_generator = OutfitImageGenerator()
            individual_images = []
            
            for outfit in outfits:
                flatlay_result = image_generator.generate_outfit_flatlay_image(outfit, occasion, season)
                if flatlay_result['success']:
                    individual_images.append({
                        'outfit': outfit,
                        'image_data': flatlay_result['image_data'],
                        'flatlay_file': flatlay_result['flatlay_image'],
                        'outfit_name': outfit.get('name', f'outfit_{occasion}_{season}')
                    })
                else:
                    logger.warning(f"Failed to generate flat-lay for outfit {outfit.get('name', 'unknown')}: {flatlay_result['error']}")
            
            return {
                'success': True,
                'individual_images': individual_images,
                'total_images': len(individual_images),
                'outfits': outfits
            }
            
        except Exception as e:
            logger.error(f"Error generating individual outfit images: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_outfit_from_items(self, items, occasion, season, name):
        """Create a basic outfit structure from items"""
        return {
            'name': name,
            'items': items,
            'occasion': occasion,
            'season': season,
            'tops': [item for item in items if item.category == 'top'],
            'bottoms': [item for item in items if item.category == 'bottom'],
            'shoes': [item for item in items if item.category == 'shoes'],
            'accessories': [item for item in items if item.category == 'accessories'],
            'outerwear': [item for item in items if item.category == 'outerwear'],
            'dresses': [item for item in items if item.category == 'dress'],
        }
    
    def _process_single_outfit(self, outfit_data):
        """Process a single outfit to generate flat-lay and mannequin images"""
        outfit, occasion, season, index = outfit_data
        try:
            logger.info(f"Processing outfit {index+1}: {outfit.get('name', 'Unknown')}")
            
            # Initialize services
            image_generator = OutfitImageGenerator()
            nanobanana_service = NanobananaMannequinService()
            
            # Generate individual flat-lay image
            flatlay_result = image_generator.generate_outfit_flatlay_image(outfit, occasion, season)
            
            if flatlay_result['success']:
                # Encode flat-lay image data as base64
                import base64
                outfit['flatlay_image_data'] = base64.b64encode(flatlay_result['image_data']).decode('utf-8')
                logger.info(f"Generated flat-lay image for outfit {index+1}")
            else:
                logger.warning(f"Failed to generate flat-lay for outfit {index+1}: {flatlay_result['error']}")
                outfit['flatlay_image_data'] = None
            
            # Generate mannequin image from the flat-lay
            if flatlay_result['success']:
                try:
                    mannequin_result = nanobanana_service.generate_mannequin_image(
                        flatlay_result['image_data'], occasion, season
                    )
                    
                    if mannequin_result['success']:
                        # Encode mannequin image data as base64
                        outfit['mannequin_image_data'] = base64.b64encode(mannequin_result['mannequin_image_data']).decode('utf-8')
                        outfit['mannequin_analysis'] = mannequin_result['analysis']
                        logger.info(f"Generated mannequin image for outfit {index+1}")
                    else:
                        logger.warning(f"Failed to generate mannequin for outfit {index+1}: {mannequin_result['error']}")
                        outfit['mannequin_image_data'] = None
                        outfit['mannequin_analysis'] = None
                        
                except Exception as e:
                    logger.error(f"Error generating mannequin for outfit {index+1}: {e}")
                    outfit['mannequin_image_data'] = None
                    outfit['mannequin_analysis'] = None
            else:
                outfit['mannequin_image_data'] = None
                outfit['mannequin_analysis'] = None
                
            return outfit, index
            
        except Exception as e:
            logger.error(f"Error processing outfit {index+1}: {e}")
            # Ensure outfit has the required fields even if processing fails
            outfit['flatlay_image_data'] = None
            outfit['mannequin_image_data'] = None
            outfit['mannequin_analysis'] = None
            return outfit, index
    
    def _process_outfits_concurrently(self, outfits, occasion, season):
        """Process all outfits concurrently using ThreadPoolExecutor"""
        if not outfits:
            return outfits
            
        logger.info(f"Starting concurrent processing of {len(outfits)} outfits")
        start_time = time.time()
        
        # Prepare data for concurrent processing
        outfit_data = [(outfit, occasion, season, i) for i, outfit in enumerate(outfits)]
        
        # Use ThreadPoolExecutor for concurrent processing
        # Limit max_workers to avoid overwhelming the API and rate limits
        # Can be configured via environment variable or settings
        max_concurrent = getattr(settings, 'OUTFIT_CONCURRENT_WORKERS', 5)
        max_workers = min(len(outfits), max_concurrent)
        
        processed_outfits = [None] * len(outfits)
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._process_single_outfit, data): data[3] 
                for data in outfit_data
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                try:
                    outfit, index = future.result()
                    processed_outfits[index] = outfit
                    completed_count += 1
                    elapsed_time = time.time() - start_time
                    logger.info(f"Completed processing outfit {index+1} ({completed_count}/{len(outfits)}) in {elapsed_time:.2f}s")
                except Exception as e:
                    index = future_to_index[future]
                    logger.error(f"Failed to process outfit {index+1}: {e}")
                    # Keep the original outfit with null image data
                    processed_outfits[index] = outfits[index]
                    processed_outfits[index]['flatlay_image_data'] = None
                    processed_outfits[index]['mannequin_image_data'] = None
                    processed_outfits[index]['mannequin_analysis'] = None
                    completed_count += 1
        
        total_time = time.time() - start_time
        logger.info(f"Completed concurrent processing of {len(outfits)} outfits in {total_time:.2f}s")
        return processed_outfits
    
    def _analyze_outfit_with_ai(self, outfit, occasion, season):
        """Use AI to analyze and score an outfit combination using LangChain"""
        try:
            # Create outfit description
            outfit_description = self._describe_outfit(outfit)
            
            # Create the prompt template with format instructions
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a professional fashion stylist and outfit analyst. Analyze outfits using all available information including colors, materials, style descriptions, occasions, seasons, and style tags. Provide detailed, structured feedback."),
                ("user", """Analyze this outfit combination for a {occasion} occasion in {season} season:

{outfit_description}

The outfit description includes detailed information about each item including:
- Primary and secondary colors
- Clothing types (shirt, pants, dress, etc.)
- Materials and fabrics
- Style descriptions and tags
- Suitable occasions and seasons
- Brand information and sizing
- Color palettes

Please evaluate the outfit considering:

1. OCCASION APPROPRIATENESS: Is this suitable for the specified {occasion} occasion? This is CRITICAL - the outfit must match the occasion requirements. Consider the individual item occasions and how they complement each other.
2. SEASON SUITABILITY: Is this appropriate for the {season} season? This is CRITICAL - the outfit must match the season requirements. Check if the materials, colors, and styles are seasonally appropriate.
3. STYLE COHESION: How well do the pieces work together based on their style descriptions, materials, and overall aesthetic?
4. COLOR HARMONY: Do the colors work well together? Consider the primary colors, color palettes, and any color schemes.
5. MATERIAL COMPATIBILITY: Do the materials and fabrics complement each other?
6. STYLE CONSISTENCY: Do the style tags and descriptions create a cohesive look?
7. OVERALL CONFIDENCE: Rate the overall outfit quality and appropriateness for the {occasion} occasion in {season} season (0-1)

IMPORTANT: The outfit must be suitable for the {occasion} occasion and {season} season. If it doesn't match these requirements, provide a low confidence score and suggest improvements.

Provide specific feedback based on the detailed item information provided.

{format_instructions}""")
            ])
            
            # Create the chain
            chain = prompt_template | self.llm | self.output_parser
            
            # Invoke the chain with the outfit data
            analysis_result = chain.invoke({
                "occasion": occasion,
                "season": season,
                "outfit_description": outfit_description,
                "format_instructions": self.output_parser.get_format_instructions()
            })
            
            # Combine outfit data with AI analysis
            outfit.update({
                'style_description': analysis_result.style_description,
                'color_scheme': analysis_result.color_scheme,
                'style_tags': analysis_result.style_tags,
                'confidence_score': analysis_result.confidence_score,
                'style_notes': analysis_result.style_notes,
                'improvement_suggestions': analysis_result.improvement_suggestions
            })
            
            return outfit
            
        except Exception as e:
            logger.error(f"Error analyzing outfit with AI: {e}")
            
            # Fallback analysis in case of error
            outfit.update({
                'style_description': f"Stylish {occasion} outfit for {season}",
                'color_scheme': [item.color for item in outfit['items']],
                'style_tags': [occasion, season],
                'confidence_score': 0.6,
                'style_notes': f"Error during analysis: {str(e)}",
                'improvement_suggestions': []
            })
            return outfit
    
    def _analyze_all_outfits_with_ai(self, outfits, occasion, season, max_outfits=5):
        """Use AI to analyze and rank all outfits in a single batch prompt"""
        try:
            # Create descriptions for all outfits
            outfit_descriptions = []
            for i, outfit in enumerate(outfits):
                outfit_description = self._describe_outfit(outfit)
                outfit_descriptions.append(f"OUTFIT {i}:\n{outfit_description}\n")
            
            all_outfits_text = "\n".join(outfit_descriptions)
            
            # Create the batch analysis prompt template
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a professional fashion stylist and outfit analyst. Analyze multiple outfits and provide detailed rankings and feedback. Consider all available information including colors, clothing types, materials, style descriptions, occasions, seasons, and style tags."),
                ("user", """Analyze these {total_outfits} outfit combinations for a {occasion} occasion in {season} season:

{all_outfits_text}

For each outfit, evaluate:
1. OCCASION APPROPRIATENESS: Is this suitable for the specified {occasion} occasion? This is CRITICAL - prioritize outfits that match the occasion requirements. Consider the individual item occasions and how they complement each other.
2. SEASON SUITABILITY: Is this appropriate for the {season} season? This is CRITICAL - prioritize outfits that match the season requirements. Check if the materials, colors, and styles are seasonally appropriate.
3. STYLE COHESION: How well do the pieces work together based on their style descriptions, materials, and overall aesthetic?
4. COLOR HARMONY: Do the colors work well together? Consider the primary colors, color palettes, and any color schemes.
5. MATERIAL COMPATIBILITY: Do the materials and fabrics complement each other?
6. STYLE CONSISTENCY: Do the style tags and descriptions create a cohesive look?
7. OVERALL CONFIDENCE: Rate the overall outfit quality and appropriateness for the {occasion} occasion in {season} season (0-1)

IMPORTANT: Prioritize outfits that are most suitable for the {occasion} occasion and {season} season. Outfits that don't match these requirements should be ranked lower.

Please:
1. Rank all outfits from best to worst (1 = best)
2. Provide detailed analysis for each outfit
3. Identify the top {max_outfits} recommendations
4. Give an overall analysis of the outfit collection and trends

{format_instructions}""")
            ])
            
            # Create the chain
            chain = prompt_template | self.llm | self.batch_output_parser
            
            # Invoke the chain with the outfit data
            analysis_result = chain.invoke({
                "total_outfits": len(outfits),
                "occasion": occasion,
                "season": season,
                "all_outfits_text": all_outfits_text,
                "max_outfits": max_outfits,
                "format_instructions": self.batch_output_parser.get_format_instructions()
            })
            
            # Convert the analysis result back to the original outfit format
            analyzed_outfits = []
            for ranking in analysis_result.outfit_rankings:
                outfit_idx = ranking.outfit_id
                if outfit_idx < len(outfits):
                    outfit = outfits[outfit_idx].copy()
                    outfit.update({
                        'style_description': ranking.style_description,
                        'color_scheme': ranking.color_scheme,
                        'style_tags': ranking.style_tags,
                        'confidence_score': ranking.confidence_score,
                        'style_notes': ranking.style_notes,
                        'improvement_suggestions': ranking.improvement_suggestions,
                        'ranking_position': ranking.ranking_position
                    })
                    analyzed_outfits.append(outfit)
            
            # Sort by ranking position (1 = best)
            analyzed_outfits.sort(key=lambda x: x.get('ranking_position', 999))
            
            # Return only the top recommendations
            top_outfits = analyzed_outfits[:max_outfits]
            
            return {
                'outfits': top_outfits,
                'overall_analysis': analysis_result.overall_analysis,
                'total_analyzed': len(outfits)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing all outfits with AI: {e}")
            
            # Fallback: return outfits with basic analysis
            fallback_outfits = []
            for i, outfit in enumerate(outfits[:max_outfits]):
                outfit.update({
                    'style_description': f"Stylish {occasion} outfit for {season}",
                    'color_scheme': [item.color for item in outfit['items']],
                    'style_tags': [occasion, season],
                    'confidence_score': 0.6,
                    'style_notes': f"Error during analysis: {str(e)}",
                    'improvement_suggestions': [],
                    'ranking_position': i + 1
                })
                fallback_outfits.append(outfit)
            
            return {
                'outfits': fallback_outfits,
                'overall_analysis': f"Analysis failed: {str(e)}",
                'total_analyzed': len(outfits)
            }
    
    def _describe_outfit(self, outfit):
        """Create a comprehensive text description of an outfit using all available database fields"""
        description_parts = []
        
        def format_item_details(item, category_name):
            """Helper function to format item details with all available information"""
            details = [f"{item.color} {category_name}"]
            
            # Add clothing type from ProcessedImage
            if hasattr(item, 'processed_image') and item.processed_image:
                clothing_type = item.processed_image.get_clothing_type_display()
                details.append(f"({clothing_type})")
            
            # Add name if available
            if item.name:
                details.append(f"({item.name})")
            
            # Add brand if available
            if item.brand:
                details.append(f"by {item.brand}")
            
            # Add material if available
            if item.material:
                details.append(f"in {item.material}")
            
            # Add size if available
            if item.size:
                details.append(f"size {item.size}")
            
            # Add style description if available
            if item.style_description:
                details.append(f"- Style: {item.style_description}")
            
            # Add style tags if available
            if item.style_tags:
                tags = item.style_tags if isinstance(item.style_tags, list) else []
                if tags:
                    details.append(f"- Tags: {', '.join(tags)}")
            
            # Add occasion and season
            details.append(f"- Occasion: {item.occasion}, Season: {item.season}")
            
            # Add color palette if available
            if item.color_palette:
                palette = item.color_palette if isinstance(item.color_palette, list) else []
                if palette:
                    details.append(f"- Color palette: {', '.join(palette)}")
            
            return " ".join(details)
        
        # Process each category
        if outfit['tops']:
            for top in outfit['tops']:
                description_parts.append(f"- {format_item_details(top, 'top')}")
        
        if outfit['bottoms']:
            for bottom in outfit['bottoms']:
                description_parts.append(f"- {format_item_details(bottom, 'bottom')}")
        
        if outfit['dresses']:
            for dress in outfit['dresses']:
                description_parts.append(f"- {format_item_details(dress, 'dress')}")
        
        if outfit['shoes']:
            for shoe in outfit['shoes']:
                description_parts.append(f"- {format_item_details(shoe, 'shoes')}")
        
        if outfit['accessories']:
            for accessory in outfit['accessories']:
                description_parts.append(f"- {format_item_details(accessory, 'accessories')}")
        
        if outfit['outerwear']:
            for outer in outfit['outerwear']:
                description_parts.append(f"- {format_item_details(outer, 'outerwear')}")
        
        return "\n".join(description_parts)
    
    def save_outfit_recommendation(self, outfit_data, user=None):
        """Save an outfit recommendation to the database"""
        try:
            # Create outfit recommendation
            outfit = OutfitRecommendation.objects.create(
                name=outfit_data['name'],
                occasion=outfit_data['occasion'],
                season=outfit_data['season'],
                style_description=outfit_data.get('style_description', ''),
                color_scheme=outfit_data.get('color_scheme', []),
                style_tags=outfit_data.get('style_tags', []),
                confidence_score=outfit_data.get('confidence_score', 0.5),
                user=user
            )
            
            # Add items to outfit
            for item in outfit_data['items']:
                OutfitItem.objects.create(
                    outfit=outfit,
                    item=item,
                    category=item.category,
                    match_score=outfit_data.get('confidence_score', 0.5),
                    style_notes=outfit_data.get('style_notes', '')
                )
            
            return {
                'success': True,
                'outfit': outfit
            }
            
        except Exception as e:
            logger.error(f"Error saving outfit recommendation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_wardrobe_item_analysis(self, wardrobe_item):
        """Update wardrobe item with AI analysis"""
        try:
            analysis_result = self.analyze_wardrobe_item(wardrobe_item)
            
            if analysis_result['success']:
                analysis = analysis_result['analysis']
                
                # Update wardrobe item with analysis
                wardrobe_item.primary_color = analysis.get('primary_color', wardrobe_item.color)
                wardrobe_item.style_description = analysis.get('style', '')
                wardrobe_item.color_palette = analysis.get('color_palette', [])
                wardrobe_item.style_tags = analysis.get('style_tags', [])
                
                # Update occasion and season if provided
                if analysis.get('suitable_occasions'):
                    # Use the first suitable occasion or keep current
                    wardrobe_item.occasion = analysis['suitable_occasions'][0]
                
                if analysis.get('suitable_seasons'):
                    # Use the first suitable season or keep current
                    wardrobe_item.season = analysis['suitable_seasons'][0]
                
                wardrobe_item.save()
                
                return {
                    'success': True,
                    'updated_item': wardrobe_item
                }
            else:
                return analysis_result
                
        except Exception as e:
            logger.error(f"Error updating wardrobe item analysis: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class ImageValidationService:
    """Service for validating uploaded images"""
    
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def validate_image_file(cls, uploaded_file):
        """Validate uploaded image file"""
        errors = []
        
        # Check file size
        if uploaded_file.size > cls.MAX_FILE_SIZE:
            errors.append(f"File size too large. Maximum size is {cls.MAX_FILE_SIZE / (1024*1024):.1f}MB")
        
        # Check file extension
        file_extension = os.path.splitext(uploaded_file.name.lower())[1]
        if file_extension not in cls.ALLOWED_EXTENSIONS:
            errors.append(f"File type not supported. Allowed types: {', '.join(cls.ALLOWED_EXTENSIONS)}")
        
        # Check if file is actually an image (basic check)
        try:
            from PIL import Image
            with Image.open(uploaded_file) as img:
                img.verify()
            # Reset file pointer
            uploaded_file.seek(0)
        except Exception:
            errors.append("Invalid image file")
        
        return errors


class OutfitImageGenerator:
    """Service for generating individual flat-lay images of outfit combinations"""
    
    def __init__(self):
        pass
    
    def generate_outfit_flatlay_image(self, outfit, occasion='casual', season='all'):
        """Generate a single flat-lay image for one outfit combination"""
        try:
            if not outfit:
                return {
                    'success': False,
                    'error': 'No outfit provided for flat-lay image generation'
                }
                
            # Collect all items from the outfit
            all_items = []
            if outfit.get('tops'):
                all_items.extend(outfit['tops'])
            if outfit.get('bottoms'):
                all_items.extend(outfit['bottoms'])
            if outfit.get('shoes'):
                all_items.extend(outfit['shoes'])
            if outfit.get('accessories'):
                all_items.extend(outfit['accessories'])
            if outfit.get('outerwear'):
                all_items.extend(outfit['outerwear'])
            if outfit.get('dresses'):
                all_items.extend(outfit['dresses'])
            
            # Outfit has items - proceed with generation
            
            if not all_items:
                return {
                    'success': False,
                    'error': 'No items found in outfit'
                }
            
            # Flat-lay image dimensions - larger canvas for bigger items
            canvas_width = 400
            canvas_height = 300
            
            # Create the flat-lay canvas
            canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
            
            # Item positioning for natural flat-lay arrangement
            item_positions = self._calculate_flatlay_positions(all_items, canvas_width, canvas_height)
            
            # Try to load a font, fallback to default if not available
            try:
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font_small = ImageFont.load_default()
            
            # Place each item in its calculated position
            for i, (item, position) in enumerate(zip(all_items, item_positions)):
                x, y, size = position
                
                # Try to get the item image
                try:
                    item_image = None
                    image_path = None
                    
                    # Try processed image first
                    if hasattr(item, 'processed_image') and item.processed_image:
                        if hasattr(item.processed_image, 'processed_image') and item.processed_image.processed_image:
                            image_path = item.processed_image.processed_image.path
                            if os.path.exists(image_path):
                                item_image = Image.open(image_path)
                        
                        # Try original image if processed image failed
                        if item_image is None and hasattr(item.processed_image, 'original_image') and item.processed_image.original_image:
                            image_path = item.processed_image.original_image.path
                            if os.path.exists(image_path):
                                item_image = Image.open(image_path)
                    
                    # Create placeholder if no image was loaded
                    if item_image is None:
                        item_image = Image.new('RGB', (size, size), '#f0f0f0')
                        draw_placeholder = ImageDraw.Draw(item_image)
                        draw_placeholder.text((size//8, size//2), item.name[:8], fill='#999999', font=font_small)
                        
                except Exception as e:
                    logger.error(f"Error loading image for item {item.name}: {e}")
                    # Create a placeholder image
                    item_image = Image.new('RGB', (size, size), '#f0f0f0')
                    draw_placeholder = ImageDraw.Draw(item_image)
                    draw_placeholder.text((size//8, size//2), item.name[:8], fill='#999999', font=font_small)
                
                # Resize the item image
                item_image = item_image.resize((size, size), Image.Resampling.LANCZOS)
                
                # Paste the item image onto the canvas
                canvas.paste(item_image, (x, y), item_image if item_image.mode == 'RGBA' else None)
            
            # Save the flat-lay image
            output_buffer = BytesIO()
            canvas.save(output_buffer, format='PNG', quality=95)
            output_buffer.seek(0)
            
            # Create a Django ContentFile
            outfit_name = outfit.get('name', f'outfit_{occasion}_{season}').replace(' ', '_').lower()
            flatlay_file = ContentFile(output_buffer.getvalue(), name=f'flatlay_{outfit_name}.png')
            
            return {
                'success': True,
                'flatlay_image': flatlay_file,
                'image_data': output_buffer.getvalue(),
                'outfit': outfit
            }
            
        except Exception as e:
            logger.error(f"Error generating outfit flat-lay image: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_outfit_composite_image(self, outfits, occasion='casual', season='all'):
        """Generate a single composite image showing multiple flat-lay outfit arrangements"""
        try:
            if not outfits:
                return {
                    'success': False,
                    'error': 'No outfits provided for composite image generation'
                }
            
            # Limit to reasonable number of outfits for display
            outfits_to_show = outfits[:6]  # Show max 6 outfits
            
            # Calculate grid dimensions
            if len(outfits_to_show) == 1:
                cols, rows = 1, 1
            elif len(outfits_to_show) == 2:
                cols, rows = 2, 1
            elif len(outfits_to_show) <= 4:
                cols, rows = 2, 2
            elif len(outfits_to_show) <= 6:
                cols, rows = 3, 2
            else:
                cols, rows = 3, 3
            
            # Individual flat-lay dimensions - larger for bigger items
            flatlay_width = 400
            flatlay_height = 300
            padding = 15
            margin = 20
            
            # Calculate total composite image size
            total_width = (flatlay_width * cols) + (padding * (cols - 1)) + (margin * 2)
            total_height = (flatlay_height * rows) + (padding * (rows - 1)) + (margin * 2) + 35  # Compact title space only
            
            # Create the composite image
            composite = Image.new('RGB', (total_width, total_height), 'white')
            draw = ImageDraw.Draw(composite)
            
            # Try to load a font
            try:
                font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font_title = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw title - more compact
            title = f"Outfit Recommendations - {occasion.title()} {season.title()}"
            title_bbox = draw.textbbox((0, 0), title, font=font_title)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (total_width - title_width) // 2
            draw.text((title_x, margin // 2), title, fill='#333333', font=font_title)
            
            # Draw each outfit as a flat-lay
            for i, outfit in enumerate(outfits_to_show):
                row = i // cols
                col = i % cols
                
                # Calculate position for this outfit's flat-lay - more compact
                x_start = margin + (col * (flatlay_width + padding))
                y_start = margin + 35 + (row * (flatlay_height + padding))
                
                # Create individual flat-lay for this outfit
                flatlay_result = self.generate_outfit_flatlay_image(outfit, occasion, season)
                
                if flatlay_result['success']:
                    # Load the flat-lay image
                    flatlay_image = Image.open(BytesIO(flatlay_result['image_data']))
                    # Resize to fit our grid
                    flatlay_image = flatlay_image.resize((flatlay_width, flatlay_height), Image.Resampling.LANCZOS)
                    
                    # Paste onto composite
                    composite.paste(flatlay_image, (x_start, y_start))
                    
                    # Draw outfit border
                    draw.rectangle([x_start, y_start, x_start + flatlay_width, y_start + flatlay_height], 
                                 outline='#cccccc', width=2)
                else:
                    # Create placeholder if flat-lay generation failed
                    placeholder = Image.new('RGB', (flatlay_width, flatlay_height), '#f0f0f0')
                    draw_placeholder = ImageDraw.Draw(placeholder)
                    draw_placeholder.text((flatlay_width//4, flatlay_height//2), f'Outfit {i+1}', fill='#999999', font=font_small)
                    composite.paste(placeholder, (x_start, y_start))
                    draw.rectangle([x_start, y_start, x_start + flatlay_width, y_start + flatlay_height], 
                                 outline='#cccccc', width=2)
            
            # Save the composite image
            output_buffer = BytesIO()
            composite.save(output_buffer, format='PNG', quality=95)
            output_buffer.seek(0)
            
            # Create a Django ContentFile
            composite_file = ContentFile(output_buffer.getvalue(), name=f'outfit_composite_{occasion}_{season}.png')
            
            return {
                'success': True,
                'composite_image': composite_file,
                'image_data': output_buffer.getvalue(),
                'outfits_shown': len(outfits_to_show)
            }
            
        except Exception as e:
            logger.error(f"Error generating outfit composite image: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_flatlay_positions(self, items, canvas_width, canvas_height):
        """Calculate natural flat-lay positions for items"""
        positions = []
        item_count = len(items)
        
        if item_count == 1:
            # Single item - make it fill almost the entire canvas
            size = min(canvas_width, canvas_height) * 9 // 10  # 90% of canvas
            x = (canvas_width - size) // 2
            y = (canvas_height - size) // 2
            positions.append((x, y, size))
            
        elif item_count == 2:
            # Two items side by side - make them much larger and closer
            size = min(canvas_width, canvas_height) * 3 // 7  # ~43% of canvas
            # Position them closer together in the center
            center_x = canvas_width // 2
            x1 = center_x - size - 10  # 10px gap between items
            x2 = center_x + 10
            y = (canvas_height - size) // 2
            positions.append((x1, y, size))
            positions.append((x2, y, size))
            
        elif item_count == 3:
            # Three items in a tight triangle formation - much larger and closer
            size = min(canvas_width, canvas_height) * 2 // 5  # 40% of canvas
            center_x, center_y = canvas_width // 2, canvas_height // 2
            
            # Top item - centered
            x1 = center_x - size // 2
            y1 = center_y - size - 5  # 5px gap
            positions.append((x1, y1, size))
            
            # Bottom left item - closer to center
            x2 = center_x - size - 5
            y2 = center_y + 5
            positions.append((x2, y2, size))
            
            # Bottom right item - closer to center
            x3 = center_x + 5
            y3 = center_y + 5
            positions.append((x3, y3, size))
            
        elif item_count == 4:
            # Four items in a tight square formation - larger and closer
            size = min(canvas_width, canvas_height) * 2 // 7  # ~28% of canvas
            center_x, center_y = canvas_width // 2, canvas_height // 2
            offset = size // 2 + 5  # Much closer spacing
            
            positions.extend([
                (center_x - offset, center_y - offset, size),  # Top left
                (center_x + offset, center_y - offset, size),  # Top right
                (center_x - offset, center_y + offset, size),  # Bottom left
                (center_x + offset, center_y + offset, size),  # Bottom right
            ])
            
        else:
            # For more than 4 items, arrange in a tight cluster
            size = min(canvas_width, canvas_height) * 2 // 9  # Larger items
            
            # Create a tight cluster in the center
            center_x, center_y = canvas_width // 2, canvas_height // 2
            import random
            random.seed(42)  # For consistent positioning
            
            for i in range(item_count):
                # Position items in a tight cluster around the center
                angle = (i * 2 * 3.14159) / item_count  # Distribute evenly in circle
                radius = size // 2
                x = int(center_x + radius * 0.5 * (i % 2 + 1) * (1 if i < item_count // 2 else -1))
                y = int(center_y + radius * 0.5 * ((i + 1) % 2) * (1 if i < item_count // 2 else -1))
                
                # Ensure items stay within canvas bounds
                x = max(size, min(canvas_width - size, x))
                y = max(size, min(canvas_height - size, y))
                
                positions.append((x, y, size))
        
        return positions
