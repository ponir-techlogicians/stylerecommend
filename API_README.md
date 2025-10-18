# Style Recommend API

A Django REST Framework API for the Style Recommend application that provides endpoints for managing processed images, wardrobe items, and outfit recommendations.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

The API is available at `http://localhost:8000/api/`

### Processed Images (`/api/processed-images/`)

- **GET** `/api/processed-images/` - List all processed images
- **POST** `/api/processed-images/` - Create a new processed image
- **GET** `/api/processed-images/{id}/` - Get specific processed image
- **PUT/PATCH** `/api/processed-images/{id}/` - Update processed image
- **DELETE** `/api/processed-images/{id}/` - Delete processed image

**Custom Actions:**
- **POST** `/api/processed-images/{id}/reprocess/` - Mark image for reprocessing
- **GET** `/api/processed-images/stats/` - Get processing statistics

**Query Parameters:**
- `status` - Filter by processing status (pending, processing, completed, failed)
- `clothing_type` - Filter by clothing type
- `completed_only=true` - Show only completed processing
- `search` - Search in processing prompt and GPT-4 analysis
- `ordering` - Order by created_at, processed_at, clothing_type

### Wardrobe Items (`/api/wardrobe-items/`)

- **GET** `/api/wardrobe-items/` - List all wardrobe items
- **POST** `/api/wardrobe-items/` - Create a new wardrobe item
- **GET** `/api/wardrobe-items/{id}/` - Get specific wardrobe item
- **PUT/PATCH** `/api/wardrobe-items/{id}/` - Update wardrobe item
- **DELETE** `/api/wardrobe-items/{id}/` - Delete wardrobe item

**Custom Actions:**
- **POST** `/api/wardrobe-items/{id}/toggle_favorite/` - Toggle favorite status
- **POST** `/api/wardrobe-items/{id}/mark_worn/` - Mark item as worn
- **GET** `/api/wardrobe-items/categories/` - Get available categories with counts
- **GET** `/api/wardrobe-items/colors/` - Get available colors with counts

**Query Parameters:**
- `category` - Filter by category (top, bottom, shoes, accessories, outerwear, dress)
- `color` - Filter by color
- `occasion` - Filter by occasion
- `season` - Filter by season
- `favorites_only=true` - Show only favorite items
- `search` - Search in name, brand, material, style_description
- `ordering` - Order by name, created_at, wear_count, last_worn

### Outfit Recommendations (`/api/outfit-recommendations/`)

- **GET** `/api/outfit-recommendations/` - List all outfit recommendations
- **POST** `/api/outfit-recommendations/` - Create a new outfit recommendation
- **GET** `/api/outfit-recommendations/{id}/` - Get specific outfit recommendation
- **PUT/PATCH** `/api/outfit-recommendations/{id}/` - Update outfit recommendation
- **DELETE** `/api/outfit-recommendations/{id}/` - Delete outfit recommendation

**Custom Actions:**
- **POST** `/api/outfit-recommendations/{id}/toggle_favorite/` - Toggle favorite status
- **POST** `/api/outfit-recommendations/{id}/rate/` - Rate outfit (1-5)
- **POST** `/api/outfit-recommendations/{id}/mark_worn/` - Mark outfit as worn
- **GET** `/api/outfit-recommendations/recommend/` - Get outfit recommendations based on criteria
- **GET** `/api/outfit-recommendations/stats/` - Get outfit statistics

**Query Parameters:**
- `occasion` - Filter by occasion
- `season` - Filter by season
- `favorites_only=true` - Show only favorite outfits
- `min_confidence` - Filter by minimum confidence score
- `search` - Search in name and style_description
- `ordering` - Order by name, created_at, confidence_score, rating

### Outfit Items (`/api/outfit-items/`)

- **GET** `/api/outfit-items/` - List all outfit items
- **POST** `/api/outfit-items/` - Create a new outfit item
- **GET** `/api/outfit-items/{id}/` - Get specific outfit item
- **PUT/PATCH** `/api/outfit-items/{id}/` - Update outfit item
- **DELETE** `/api/outfit-items/{id}/` - Delete outfit item

**Query Parameters:**
- `outfit` - Filter by outfit ID
- `item` - Filter by wardrobe item ID
- `category` - Filter by category
- `ordering` - Order by match_score, category

## Data Models

### ProcessedImage
- `id` - Unique identifier
- `clothing_type` - Type of clothing (jacket, shirt, tshirt, pants, etc.)
- `original_image` - Original uploaded image
- `processed_image` - AI processed image
- `status` - Processing status (pending, processing, completed, failed)
- `processing_prompt` - Prompt used for AI processing
- `error_message` - Error message if processing failed
- `created_at` - Creation timestamp
- `processed_at` - Processing completion timestamp
- `openai_response_id` - OpenAI API response ID
- `gpt4_analysis` - GPT-4 Vision analysis

### WardrobeItem
- `id` - Unique identifier
- `processed_image` - Related processed image
- `name` - Custom name for the item
- `category` - Category (top, bottom, shoes, accessories, outerwear, dress)
- `color` - Primary color
- `brand` - Brand name
- `size` - Size of the item
- `material` - Material/fabric type
- `occasion` - Suitable occasion
- `season` - Suitable season
- `style_description` - AI-generated style description
- `color_palette` - Extracted color palette (JSON)
- `style_tags` - Style tags for matching (JSON)
- `is_favorite` - Favorite status
- `last_worn` - Last time worn
- `wear_count` - Number of times worn
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### OutfitRecommendation
- `id` - Unique identifier
- `name` - Name for the outfit
- `occasion` - Suitable occasion
- `season` - Suitable season
- `style_description` - AI-generated description
- `color_scheme` - Color scheme analysis (JSON)
- `style_tags` - Style tags (JSON)
- `confidence_score` - AI confidence score (0-1)
- `is_favorite` - Favorite status
- `rating` - User rating (1-5)
- `last_worn` - Last time worn
- `wear_count` - Number of times worn
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### OutfitItem
- `id` - Unique identifier
- `outfit` - Related outfit recommendation
- `item` - Related wardrobe item
- `category` - Role in the outfit
- `match_score` - How well item matches outfit (0-1)
- `style_notes` - AI notes about item in outfit

## Authentication

Currently, the API uses `AllowAny` permissions for all endpoints. In production, you should implement proper authentication using:

- Token Authentication
- Session Authentication
- JWT Authentication

## CORS

CORS is enabled for all origins in development. Configure `CORS_ALLOWED_ORIGINS` in production.

## Pagination

All list endpoints support pagination with a default page size of 20 items.

## Example Usage

### Create a Processed Image
```bash
curl -X POST http://localhost:8000/api/processed-images/ \
  -H "Content-Type: multipart/form-data" \
  -F "clothing_type=shirt" \
  -F "processing_prompt=Convert this to a wardrobe item" \
  -F "original_image=@/path/to/image.jpg"
```

### Get Wardrobe Items by Category
```bash
curl "http://localhost:8000/api/wardrobe-items/?category=top&color=blue"
```

### Create an Outfit Recommendation
```bash
curl -X POST http://localhost:8000/api/outfit-recommendations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Casual Blue Outfit",
    "occasion": "casual",
    "season": "summer",
    "style_description": "A comfortable casual outfit perfect for summer days",
    "confidence_score": 0.85,
    "items": [
      {
        "item_id": 1,
        "category": "top",
        "match_score": 0.9,
        "style_notes": "Perfect blue shirt for casual wear"
      },
      {
        "item_id": 2,
        "category": "bottom",
        "match_score": 0.8,
        "style_notes": "Comfortable jeans that complement the shirt"
      }
    ]
  }'
```

### Get Outfit Recommendations
```bash
curl "http://localhost:8000/api/outfit-recommendations/recommend/?occasion=casual&season=summer"
```

## Development

To add new endpoints or modify existing ones:

1. Update the serializers in `api/serializers.py`
2. Update the viewsets in `api/views.py`
3. Update the URL routing in `api/urls.py`
4. Test the changes with the Django development server

## Production Considerations

1. Set `DEBUG = False` in settings
2. Configure proper authentication
3. Set up CORS for specific origins
4. Use a production database (PostgreSQL, MySQL)
5. Set up static file serving
6. Configure logging
7. Set up monitoring and error tracking
