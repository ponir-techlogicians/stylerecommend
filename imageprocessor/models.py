from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import os


def upload_to_original(instance, filename):
    """Generate upload path for original images"""
    return f'original_images/{filename}'


def upload_to_processed(instance, filename):
    """Generate upload path for processed images"""
    return f'processed_images/{filename}'


class ProcessedImage(models.Model):
    """Model to store information about processed images"""
    
    CLOTHING_TYPE_CHOICES = [
        ('jacket', 'Jacket'),
        ('shirt', 'Shirt'),
        ('tshirt', 'Tshirt'),
        ('pants', 'Pants'),
        ('dress', 'Dress'),
        ('sweater', 'Sweater'),
        ('hoodie', 'Hoodie'),
        ('coat', 'Coat'),
        ('blouse', 'Blouse'),
        ('skirt', 'Skirt'),
        ('shorts', 'Shorts'),
        ('shoes', 'Shoes'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Basic information
    clothing_type = models.CharField(
        max_length=20,
        choices=CLOTHING_TYPE_CHOICES,
        help_text="Type of clothing item"
    )
    original_image = models.ImageField(
        upload_to=upload_to_original,
        help_text="Original uploaded image"
    )
    processed_image = models.ImageField(
        upload_to=upload_to_processed,
        blank=True,
        null=True,
        help_text="AI processed image"
    )
    
    # Processing information
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Processing status"
    )
    processing_prompt = models.TextField(
        help_text="Prompt used for AI processing"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if processing failed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # OpenAI response data
    openai_response_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="OpenAI API response ID"
    )
    gpt4_analysis = models.TextField(
        blank=True,
        null=True,
        help_text="GPT-4 Vision analysis of the image"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Processed Image"
        verbose_name_plural = "Processed Images"
    
    def __str__(self):
        return f"{self.get_clothing_type_display()} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_filename(self):
        """Get the original filename without path"""
        return os.path.basename(self.original_image.name)
    
    def is_processing_complete(self):
        """Check if processing is complete"""
        return self.status == 'completed' and self.processed_image
    
    def get_processing_duration(self):
        """Get processing duration if completed"""
        if self.processed_at and self.created_at:
            return self.processed_at - self.created_at
        return None


class WardrobeItem(models.Model):
    """Model to store wardrobe items from processed images"""
    
    CATEGORY_CHOICES = [
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('shoes', 'Shoes'),
        ('accessories', 'Accessories'),
        ('outerwear', 'Outerwear'),
        ('dress', 'Dress'),
    ]
    
    COLOR_CHOICES = [
        ('black', 'Black'),
        ('white', 'White'),
        ('gray', 'Gray'),
        ('navy', 'Navy'),
        ('blue', 'Blue'),
        ('red', 'Red'),
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('orange', 'Orange'),
        ('purple', 'Purple'),
        ('pink', 'Pink'),
        ('brown', 'Brown'),
        ('beige', 'Beige'),
        ('cream', 'Cream'),
        ('multicolor', 'Multicolor'),
        ('other', 'Other'),
    ]
    
    OCCASION_CHOICES = [
        ('casual', 'Casual'),
        ('formal', 'Formal'),
        ('business', 'Business'),
        ('party', 'Party'),
        ('sport', 'Sport'),
        ('evening', 'Evening'),
        ('weekend', 'Weekend'),
        ('travel', 'Travel'),
    ]
    
    # Link to processed image
    processed_image = models.OneToOneField(
        ProcessedImage,
        on_delete=models.CASCADE,
        related_name='wardrobe_item'
    )
    
    # Wardrobe item details
    name = models.CharField(max_length=200, help_text="Custom name for this item")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Category of clothing item"
    )
    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        help_text="Primary color of the item"
    )
    brand = models.CharField(max_length=100, blank=True, null=True, help_text="Brand name")
    size = models.CharField(max_length=20, blank=True, null=True, help_text="Size of the item")
    material = models.CharField(max_length=100, blank=True, null=True, help_text="Material/fabric type")
    
    # Style attributes
    occasion = models.CharField(
        max_length=20,
        choices=OCCASION_CHOICES,
        default='casual',
        help_text="Suitable occasion for this item"
    )
    season = models.CharField(
        max_length=20,
        choices=[('spring', 'Spring'), ('summer', 'Summer'), ('fall', 'Fall'), ('winter', 'Winter'), ('all', 'All Season')],
        default='all',
        help_text="Season this item is suitable for"
    )
    
    # AI analysis
    style_description = models.TextField(
        blank=True,
        null=True,
        help_text="AI-generated style description"
    )
    color_palette = models.JSONField(
        blank=True,
        null=True,
        help_text="Extracted color palette"
    )
    style_tags = models.JSONField(
        blank=True,
        null=True,
        help_text="Style tags for matching"
    )
    
    # User preferences
    is_favorite = models.BooleanField(default=False, help_text="Mark as favorite item")
    last_worn = models.DateField(blank=True, null=True, help_text="Last time this item was worn")
    wear_count = models.PositiveIntegerField(default=0, help_text="Number of times worn")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Wardrobe Item"
        verbose_name_plural = "Wardrobe Items"
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def get_image_url(self):
        """Get the processed image URL"""
        if self.processed_image and self.processed_image.processed_image:
            return self.processed_image.processed_image.url
        return None
    
    def get_original_image_url(self):
        """Get the original image URL"""
        if self.processed_image and self.processed_image.original_image:
            return self.processed_image.original_image.url
        return None


class OutfitRecommendation(models.Model):
    """Model to store AI-generated outfit recommendations"""
    
    OCCASION_CHOICES = [
        ('casual', 'Casual'),
        ('formal', 'Formal'),
        ('business', 'Business'),
        ('party', 'Party'),
        ('sport', 'Sport'),
        ('evening', 'Evening'),
        ('weekend', 'Weekend'),
        ('travel', 'Travel'),
        ('date', 'Date'),
        ('work', 'Work'),
    ]
    
    SEASON_CHOICES = [
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall'),
        ('winter', 'Winter'),
        ('all', 'All Season'),
    ]
    
    # Outfit details
    name = models.CharField(max_length=200, help_text="Name for this outfit")
    occasion = models.CharField(
        max_length=20,
        choices=OCCASION_CHOICES,
        help_text="Occasion this outfit is suitable for"
    )
    season = models.CharField(
        max_length=20,
        choices=SEASON_CHOICES,
        help_text="Season this outfit is suitable for"
    )
    
    # Outfit items (many-to-many relationship)
    items = models.ManyToManyField(
        WardrobeItem,
        through='OutfitItem',
        related_name='outfits'
    )
    
    # AI analysis
    style_description = models.TextField(
        help_text="AI-generated description of the outfit"
    )
    color_scheme = models.JSONField(
        blank=True,
        null=True,
        help_text="Color scheme analysis"
    )
    style_tags = models.JSONField(
        blank=True,
        null=True,
        help_text="Style tags for this outfit"
    )
    confidence_score = models.FloatField(
        default=0.0,
        help_text="AI confidence score for this recommendation (0-1)"
    )
    
    # User interaction
    is_favorite = models.BooleanField(default=False, help_text="Mark as favorite outfit")
    rating = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="User rating (1-5)"
    )
    last_worn = models.DateField(blank=True, null=True, help_text="Last time this outfit was worn")
    wear_count = models.PositiveIntegerField(default=0, help_text="Number of times worn")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-confidence_score', '-created_at']
        verbose_name = "Outfit Recommendation"
        verbose_name_plural = "Outfit Recommendations"
    
    def __str__(self):
        return f"{self.name} - {self.get_occasion_display()}"
    
    def get_top_items(self):
        """Get top items in this outfit"""
        return self.items.filter(outfititem__category='top')
    
    def get_bottom_items(self):
        """Get bottom items in this outfit"""
        return self.items.filter(outfititem__category='bottom')
    
    def get_shoe_items(self):
        """Get shoe items in this outfit"""
        return self.items.filter(outfititem__category='shoes')
    
    def get_accessory_items(self):
        """Get accessory items in this outfit"""
        return self.items.filter(outfititem__category='accessories')
    
    def get_outerwear_items(self):
        """Get outerwear items in this outfit"""
        return self.items.filter(outfititem__category='outerwear')


class OutfitItem(models.Model):
    """Through model for outfit items with additional metadata"""
    
    outfit = models.ForeignKey(OutfitRecommendation, on_delete=models.CASCADE)
    item = models.ForeignKey(WardrobeItem, on_delete=models.CASCADE)
    
    # Item role in the outfit
    category = models.CharField(
        max_length=20,
        choices=WardrobeItem.CATEGORY_CHOICES,
        help_text="Role of this item in the outfit"
    )
    
    # AI analysis for this specific combination
    match_score = models.FloatField(
        default=0.0,
        help_text="How well this item matches the outfit (0-1)"
    )
    style_notes = models.TextField(
        blank=True,
        null=True,
        help_text="AI notes about this item in the outfit"
    )
    
    class Meta:
        unique_together = ['outfit', 'item']
        verbose_name = "Outfit Item"
        verbose_name_plural = "Outfit Items"
    
    def __str__(self):
        return f"{self.outfit.name} - {self.item.name}"