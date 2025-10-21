import os
import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db.models import Q

from .models import ProcessedImage, WardrobeItem, OutfitRecommendation, OutfitItem
from .services import OpenAIImageProcessor, ImageValidationService, StyleRecommendationService, NanobananaMannequinService
from .forms import WardrobeItemForm, OutfitRecommendationForm, OutfitSearchForm, WardrobeItemSearchForm, ConvertToWardrobeForm

logger = logging.getLogger(__name__)


class ImageUploadView(LoginRequiredMixin, View):
    """View for uploading and processing images"""
    
    def get(self, request):
        """Display the upload form"""
        return render(request, 'imageprocessor/upload.html')
    
    def post(self, request):
        """Handle image upload and processing"""
        try:
            # Get form data
            clothing_type = request.POST.get('clothing_type', '').lower()
            uploaded_file = request.FILES.get('image')
            
            # Validate input
            if not uploaded_file:
                messages.error(request, 'Please select an image file.')
                return render(request, 'imageprocessor/upload.html')
            
            if not clothing_type:
                messages.error(request, 'Please select a clothing type.')
                return render(request, 'imageprocessor/upload.html')
            
            # Validate the image file
            validation_errors = ImageValidationService.validate_image_file(uploaded_file)
            if validation_errors:
                for error in validation_errors:
                    messages.error(request, error)
                return render(request, 'imageprocessor/upload.html')
            
            # Create ProcessedImage instance
            processed_image = ProcessedImage.objects.create(
                user=request.user,
                clothing_type=clothing_type,
                original_image=uploaded_file,
                processing_prompt=OpenAIImageProcessor().generate_clothing_prompt(clothing_type),
                status='pending'
            )
            
            # Process the image asynchronously (in a real app, use Celery)
            self.process_image_async(processed_image.id)
            
            messages.success(request, 'Image uploaded successfully! Processing will begin shortly.')
            return HttpResponseRedirect(reverse('imageprocessor:result', args=[processed_image.id]))
            
        except Exception as e:
            logger.error(f"Error in ImageUploadView: {e}")
            messages.error(request, 'An error occurred while uploading the image.')
            return render(request, 'imageprocessor/upload.html')
    
    def process_image_async(self, image_id):
        """Process image with Gemini API (simplified async processing)"""
        try:
            processed_image = ProcessedImage.objects.get(id=image_id)
            processed_image.status = 'processing'
            processed_image.save()
            
            # Initialize Gemini processor
            try:
                from .services import GeminiImageProcessor
                processor = GeminiImageProcessor()
            except ValueError as e:
                logger.error(f"Gemini API key error: {e}")
                processed_image.status = 'failed'
                processed_image.error_message = str(e)
                processed_image.save()
                return
            
            # Get the full path to the original image
            original_image_path = processed_image.original_image.path
            
            # Process the image with Gemini
            result = processor.process_image_with_gemini(original_image_path, processed_image.clothing_type)
            
            if result['success']:
                # Save the processed image
                from .services import OpenAIImageProcessor
                openai_processor = OpenAIImageProcessor()
                processed_file = openai_processor.save_processed_image(
                    result['processed_image_data'],
                    processed_image.original_image.name
                )
                
                # Update the model
                processed_image.processed_image = processed_file
                processed_image.status = 'completed'
                processed_image.openai_response_id = result.get('response_id')
                processed_image.gpt4_analysis = result.get('analysis', '')
                processed_image.save()
                
                # Automatically create wardrobe item
                self.create_wardrobe_item_automatically(processed_image)
                
                logger.info(f"Successfully processed image {image_id}")
            else:
                processed_image.status = 'failed'
                processed_image.error_message = result.get('error', 'Unknown error')
                processed_image.save()
                
                logger.error(f"Failed to process image {image_id}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error processing image {image_id}: {e}")
            try:
                processed_image = ProcessedImage.objects.get(id=image_id)
                processed_image.status = 'failed'
                processed_image.error_message = str(e)
                processed_image.save()
            except:
                pass
    
    def create_wardrobe_item_automatically(self, processed_image):
        """Automatically create a wardrobe item from processed image using ChatGPT analysis"""
        try:
            # Check if wardrobe item already exists
            if hasattr(processed_image, 'wardrobe_item'):
                logger.info(f"Wardrobe item already exists for image {processed_image.id}")
                return
            
            # Analyze the image with ChatGPT to get structured data
            try:
                openai_processor = OpenAIImageProcessor()
                analysis_result = openai_processor.analyze_clothing_image(
                    processed_image.original_image.path, 
                    processed_image.clothing_type
                )
                
                if analysis_result['success']:
                    analysis_data = analysis_result['analysis']
                    
                    # Map types to wardrobe category
                    type_mapping = {
                        'top': 'top',
                        'bottom': 'bottom', 
                        'shoes': 'shoes',
                        'watch': 'accessories',
                        'accessories': 'accessories',
                        'outerwear': 'outerwear',
                        'dress': 'dress',
                    }
                    
                    # Map color to wardrobe color choices
                    color_mapping = {
                        'black': 'black',
                        'white': 'white',
                        'gray': 'gray',
                        'grey': 'gray',
                        'navy': 'navy',
                        'blue': 'blue',
                        'red': 'red',
                        'green': 'green',
                        'yellow': 'yellow',
                        'orange': 'orange',
                        'purple': 'purple',
                        'pink': 'pink',
                        'brown': 'brown',
                        'beige': 'beige',
                        'cream': 'cream'
                    }
                    
                    # Map occasion to wardrobe occasion choices
                    occasion_mapping = {
                        'casual': 'casual',
                        'formal': 'formal',
                        'business': 'business',
                        'party': 'party',
                        'sport': 'sport',
                        'evening': 'evening'
                    }
                    
                    # Map season to wardrobe season choices
                    season_mapping = {
                        'spring': 'spring',
                        'summer': 'summer',
                        'fall': 'fall',
                        'autumn': 'fall',
                        'winter': 'winter',
                        'all': 'all'
                    }
                    
                    # Prefer the user's selected clothing_type for category
                    user_selected_category = {
                        'jacket': 'outerwear',
                        'shirt': 'top',
                        'tshirt': 'top',
                        'pants': 'bottom',
                        'dress': 'dress',
                        'sweater': 'top',
                        'hoodie': 'top',
                        'coat': 'outerwear',
                        'blouse': 'top',
                        'skirt': 'bottom',
                        'shorts': 'bottom',
                        'shoes': 'shoes',
                        'other': 'accessories',
                    }.get(processed_image.clothing_type, 'accessories')

                    ai_type = (analysis_data.get('type') or '').lower().strip()
                    ai_category = type_mapping.get(ai_type)

                    # Use AI category only if it exists and matches the user's high-level category; otherwise keep user's selection
                    category = ai_category if ai_category == user_selected_category else user_selected_category
                    color = color_mapping.get(analysis_data.get('color', '').lower(), analysis_data.get('color', '').lower())
                    occasion = occasion_mapping.get(analysis_data.get('occasion', '').lower(), 'casual')
                    season = season_mapping.get(analysis_data.get('season', '').lower(), 'all')
                    material = analysis_data.get('material', 'unknown')
                    style = analysis_data.get('style', 'casual')
                    
                    # Generate a name; base it on the resolved category to avoid mismatched labels
                    from django.utils import timezone
                    timestamp = timezone.now().strftime('%Y%m%d_%H%M')
                    resolved_type_for_name = ai_type if type_mapping.get(ai_type) == category else processed_image.clothing_type
                    name = f"{color.title()} {resolved_type_for_name.title()} {timestamp}"
                    
                    # Create wardrobe item with AI analysis data
                    wardrobe_item = WardrobeItem.objects.create(
                        user=processed_image.user,
                        processed_image=processed_image,
                        name=name,
                        category=category,
                        color=color,
                        material=material,
                        occasion=occasion,
                        season=season,
                        style_description=style
                    )
                    
                    logger.info(f"Successfully created wardrobe item {wardrobe_item.id} with AI analysis for image {processed_image.id}")
                    
                else:
                    # Fallback to default creation if AI analysis fails
                    logger.warning(f"AI analysis failed for image {processed_image.id}: {analysis_result.get('error')}")
                    self._create_wardrobe_item_fallback(processed_image)
                    
            except Exception as e:
                logger.error(f"Error in AI analysis for image {processed_image.id}: {e}")
                self._create_wardrobe_item_fallback(processed_image)
            
        except Exception as e:
            logger.error(f"Error creating wardrobe item for image {processed_image.id}: {e}")
    
    def _create_wardrobe_item_fallback(self, processed_image):
        """Fallback method to create wardrobe item with default values"""
        try:
            # Map clothing types to wardrobe categories
            category_mapping = {
                'jacket': 'outerwear',
                'shirt': 'top',
                'tshirt': 'top',
                'pants': 'bottom',
                'dress': 'dress',
                'sweater': 'top',
                'hoodie': 'top',
                'coat': 'outerwear',
                'blouse': 'top',
                'skirt': 'bottom',
                'shorts': 'bottom',
                'shoes': 'shoes',
                'other': 'accessories',
            }
            
            # Get category from clothing type
            category = category_mapping.get(processed_image.clothing_type, 'accessories')
            
            # Generate a name based on clothing type and timestamp
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d_%H%M')
            name = f"{processed_image.get_clothing_type_display()} {timestamp}"
            
            # Create wardrobe item with default values
            wardrobe_item = WardrobeItem.objects.create(
                user=processed_image.user,
                processed_image=processed_image,
                name=name,
                category=category,
                color='other',  # Default color
                occasion='casual',  # Default occasion
                season='all'  # Default season
            )
            
            logger.info(f"Successfully created wardrobe item {wardrobe_item.id} with fallback method for image {processed_image.id}")
            
        except Exception as e:
            logger.error(f"Error in fallback wardrobe item creation for image {processed_image.id}: {e}")


class ImageResultView(LoginRequiredMixin, View):
    """View for displaying processing results"""
    
    def get(self, request, image_id):
        """Display the processing result"""
        processed_image = get_object_or_404(ProcessedImage, id=image_id, user=request.user)
        
        context = {
            'processed_image': processed_image,
            'is_processing_complete': processed_image.is_processing_complete(),
            'processing_duration': processed_image.get_processing_duration(),
        }
        
        return render(request, 'imageprocessor/result.html', context)


class ImageListView(LoginRequiredMixin, View):
    """View for listing all processed images"""
    
    def get(self, request):
        """Display list of all processed images"""
        processed_images = ProcessedImage.objects.filter(user=request.user)
        
        context = {
            'processed_images': processed_images,
        }
        
        return render(request, 'imageprocessor/list.html', context)


class ImageDetailView(LoginRequiredMixin, View):
    """View for displaying detailed information about a processed image"""
    
    def get(self, request, image_id):
        """Display detailed information about a processed image"""
        processed_image = get_object_or_404(ProcessedImage, id=image_id, user=request.user)
        
        context = {
            'processed_image': processed_image,
        }
        
        return render(request, 'imageprocessor/detail.html', context)


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def check_processing_status(request, image_id):
    """API endpoint to check processing status"""
    try:
        processed_image = get_object_or_404(ProcessedImage, id=image_id, user=request.user)
        
        return JsonResponse({
            'status': processed_image.status,
            'is_complete': processed_image.is_processing_complete(),
            'error_message': processed_image.error_message,
            'processed_image_url': processed_image.processed_image.url if processed_image.processed_image else None,
        })
    except Exception as e:
        logger.error(f"Error checking processing status: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# Wardrobe Management Views

class WardrobeListView(LoginRequiredMixin, View):
    """View for displaying all wardrobe items"""
    
    def get(self, request):
        """Display wardrobe items with search and filter options"""
        search_form = WardrobeItemSearchForm(request.GET)
        wardrobe_items = WardrobeItem.objects.filter(user=request.user)
        
        # Apply filters
        if search_form.is_valid():
            if search_form.cleaned_data.get('category'):
                wardrobe_items = wardrobe_items.filter(category=search_form.cleaned_data['category'])
            
            if search_form.cleaned_data.get('color'):
                wardrobe_items = wardrobe_items.filter(color=search_form.cleaned_data['color'])
            
            if search_form.cleaned_data.get('occasion'):
                wardrobe_items = wardrobe_items.filter(occasion=search_form.cleaned_data['occasion'])
            
            if search_form.cleaned_data.get('search'):
                search_term = search_form.cleaned_data['search']
                wardrobe_items = wardrobe_items.filter(
                    Q(name__icontains=search_term) |
                    Q(brand__icontains=search_term) |
                    Q(material__icontains=search_term)
                )
            
            if search_form.cleaned_data.get('favorites_only'):
                wardrobe_items = wardrobe_items.filter(is_favorite=True)
        
        # Group items by category for better display
        items_by_category = {}
        for item in wardrobe_items:
            category = item.get_category_display()
            if category not in items_by_category:
                items_by_category[category] = []
            items_by_category[category].append(item)
        
        context = {
            'search_form': search_form,
            'items_by_category': items_by_category,
            'total_items': wardrobe_items.count(),
        }
        
        return render(request, 'imageprocessor/wardrobe_list.html', context)


class WardrobeItemDetailView(LoginRequiredMixin, View):
    """View for displaying individual wardrobe item details"""
    
    def get(self, request, item_id):
        """Display wardrobe item details"""
        item = get_object_or_404(WardrobeItem, id=item_id, user=request.user)
        
        # Get outfits that include this item
        outfits_with_item = OutfitRecommendation.objects.filter(items=item)
        
        context = {
            'item': item,
            'outfits_with_item': outfits_with_item,
        }
        
        return render(request, 'imageprocessor/wardrobe_item_detail.html', context)


class WardrobeItemEditView(LoginRequiredMixin, View):
    """View for editing wardrobe items"""
    
    def get(self, request, item_id):
        """Display edit form"""
        item = get_object_or_404(WardrobeItem, id=item_id, user=request.user)
        form = WardrobeItemForm(instance=item)
        
        context = {
            'form': form,
            'item': item,
        }
        
        return render(request, 'imageprocessor/wardrobe_item_edit.html', context)
    
    def post(self, request, item_id):
        """Handle form submission"""
        item = get_object_or_404(WardrobeItem, id=item_id, user=request.user)
        form = WardrobeItemForm(request.POST, instance=item)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Wardrobe item updated successfully!')
            return HttpResponseRedirect(reverse('wardrobe_item_detail', args=[item_id]))
        
        context = {
            'form': form,
            'item': item,
        }
        
        return render(request, 'imageprocessor/wardrobe_item_edit.html', context)


class ConvertToWardrobeView(LoginRequiredMixin, View):
    """View for converting processed images to wardrobe items"""
    
    def get(self, request, image_id):
        """Display conversion form"""
        processed_image = get_object_or_404(ProcessedImage, id=image_id, user=request.user)
        
        if processed_image.status != 'completed':
            messages.error(request, 'Image must be processed before adding to wardrobe.')
            return HttpResponseRedirect(reverse('image_detail', args=[image_id]))
        
        # Check if already converted
        if hasattr(processed_image, 'wardrobe_item'):
            messages.info(request, 'This image is already in your wardrobe.')
            return HttpResponseRedirect(reverse('wardrobe_item_detail', args=[processed_image.wardrobe_item.id]))
        
        form = ConvertToWardrobeForm()
        form.fields['processed_image'].initial = processed_image
        
        context = {
            'form': form,
            'processed_image': processed_image,
        }
        
        return render(request, 'imageprocessor/convert_to_wardrobe.html', context)
    
    def post(self, request, image_id):
        """Handle conversion"""
        processed_image = get_object_or_404(ProcessedImage, id=image_id, user=request.user)
        form = ConvertToWardrobeForm(request.POST)
        
        if form.is_valid():
            try:
                # Create wardrobe item
                wardrobe_item = WardrobeItem.objects.create(
                    user=request.user,
                    processed_image=processed_image,
                    name=form.cleaned_data['name'],
                    category=form.cleaned_data['category'],
                    color=form.cleaned_data['color'],
                    brand=form.cleaned_data['brand'],
                    size=form.cleaned_data['size'],
                    material=form.cleaned_data['material'],
                    occasion=form.cleaned_data['occasion'],
                    season=form.cleaned_data['season']
                )
                
                messages.success(request, 'Item added to wardrobe successfully!')
                return HttpResponseRedirect(reverse('wardrobe_item_detail', args=[wardrobe_item.id]))
                
            except Exception as e:
                logger.error(f"Error creating wardrobe item: {e}")
                messages.error(request, 'Error adding item to wardrobe. Please try again.')
        
        context = {
            'form': form,
            'processed_image': processed_image,
        }
        
        return render(request, 'imageprocessor/convert_to_wardrobe.html', context)


# Outfit Recommendation Views

class OutfitRecommendationView(LoginRequiredMixin, View):
    """View for generating and displaying outfit recommendations"""
    
    def get(self, request):
        """Display outfit recommendation form and results"""
        search_form = OutfitSearchForm(request.GET)
        outfits = []
        composite_image_data = None
        mannequin_image_data = None
        overall_analysis = None
        
        if search_form.is_valid():
            occasion = search_form.cleaned_data.get('occasion', 'casual')
            season = search_form.cleaned_data.get('season', 'all')
            max_outfits = search_form.cleaned_data.get('max_outfits', 5)
            
            try:
                style_service = StyleRecommendationService()
                result = style_service.generate_outfit_recommendations(
                    user=request.user,
                    occasion=occasion,
                    season=season,
                    max_outfits=max_outfits
                )
                
                if result['success']:
                    outfits = result['outfits']
                    composite_image_data = result.get('composite_image_data')
                    mannequin_image_data = result.get('mannequin_image_data')
                    overall_analysis = result.get('overall_analysis')
                    
                    # Debug logging
                    logger.info(f"Result keys: {result.keys()}")
                    logger.info(f"Composite image data present: {composite_image_data is not None}")
                    logger.info(f"Mannequin image data present: {mannequin_image_data is not None}")
                    
                    if composite_image_data:
                        import base64
                        composite_image_data = base64.b64encode(composite_image_data).decode('utf-8')
                        logger.info("Composite image data encoded successfully")
                    
                    if mannequin_image_data:
                        import base64
                        mannequin_image_data = base64.b64encode(mannequin_image_data).decode('utf-8')
                        logger.info("Mannequin image data encoded successfully")
                    else:
                        logger.warning("No mannequin image data received")
                    
                    messages.success(request, f'Generated {len(outfits)} outfit recommendations!')
                else:
                    messages.error(request, result['error'])
                    
            except Exception as e:
                logger.error(f"Error generating outfit recommendations: {e}")
                messages.error(request, 'Error generating outfit recommendations. Please try again.')
        
        context = {
            'search_form': search_form,
            'outfits': outfits,
            'composite_image_data': composite_image_data,
            'mannequin_image_data': mannequin_image_data,
            'overall_analysis': overall_analysis,
        }

        print('mannequin_image_data', mannequin_image_data)
        
        return render(request, 'imageprocessor/outfit_recommendations.html', context)
    
    def post(self, request):
        """Handle saving outfit recommendations"""
        outfit_data = request.POST.get('outfit_data')
        
        if outfit_data:
            try:
                import json
                outfit_json = json.loads(outfit_data)
                
                style_service = StyleRecommendationService()
                result = style_service.save_outfit_recommendation(outfit_json, user=request.user)
                
                if result['success']:
                    messages.success(request, 'Outfit saved successfully!')
                    return JsonResponse({'success': True, 'outfit_id': result['outfit'].id})
                else:
                    return JsonResponse({'success': False, 'error': result['error']})
                    
            except Exception as e:
                logger.error(f"Error saving outfit: {e}")
                return JsonResponse({'success': False, 'error': str(e)})
        
        return JsonResponse({'success': False, 'error': 'No outfit data provided'})


class OutfitDetailView(LoginRequiredMixin, View):
    """View for displaying individual outfit details"""
    
    def get(self, request, outfit_id):
        """Display outfit details"""
        outfit = get_object_or_404(OutfitRecommendation, id=outfit_id, user=request.user)
        
        context = {
            'outfit': outfit,
        }
        
        return render(request, 'imageprocessor/outfit_detail.html', context)


class SavedOutfitsView(LoginRequiredMixin, View):
    """View for displaying saved outfit recommendations"""
    
    def get(self, request):
        """Display saved outfits"""
        outfits = OutfitRecommendation.objects.filter(user=request.user).order_by('-created_at')
        
        # Apply filters if provided
        occasion = request.GET.get('occasion')
        season = request.GET.get('season')
        
        if occasion:
            outfits = outfits.filter(occasion=occasion)
        
        if season:
            outfits = outfits.filter(season=season)
        
        context = {
            'outfits': outfits,
        }
        
        return render(request, 'imageprocessor/saved_outfits.html', context)


# AJAX Views

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def toggle_favorite_item(request, item_id):
    """Toggle favorite status of a wardrobe item"""
    try:
        item = get_object_or_404(WardrobeItem, id=item_id, user=request.user)
        item.is_favorite = not item.is_favorite
        item.save()
        
        return JsonResponse({
            'success': True,
            'is_favorite': item.is_favorite
        })
    except Exception as e:
        logger.error(f"Error toggling favorite item: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def analyze_wardrobe_item(request, item_id):
    """Analyze wardrobe item with AI"""
    try:
        item = get_object_or_404(WardrobeItem, id=item_id, user=request.user)
        
        style_service = StyleRecommendationService()
        result = style_service.update_wardrobe_item_analysis(item)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'message': 'Item analyzed successfully!',
                'updated_item': {
                    'style_description': item.style_description,
                    'style_tags': item.style_tags,
                    'color_palette': item.color_palette
                }
            })
        else:
            return JsonResponse({'success': False, 'error': result['error']})
            
    except Exception as e:
        logger.error(f"Error analyzing wardrobe item: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def rate_outfit(request, outfit_id):
    """Rate an outfit recommendation"""
    try:
        outfit = get_object_or_404(OutfitRecommendation, id=outfit_id, user=request.user)
        rating = int(request.POST.get('rating', 0))
        
        if 1 <= rating <= 5:
            outfit.rating = rating
            outfit.save()
            
            return JsonResponse({
                'success': True,
                'rating': rating,
                'message': 'Outfit rated successfully!'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Rating must be between 1 and 5'})
            
    except Exception as e:
        logger.error(f"Error rating outfit: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


def register(request):
    """User registration view using Django's UserCreationForm"""
    if request.user.is_authenticated:
        return redirect('imageprocessor:upload')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})