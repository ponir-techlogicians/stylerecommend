from rest_framework import serializers
from imageprocessor.models import ProcessedImage, WardrobeItem, OutfitRecommendation, OutfitItem


class ProcessedImageSerializer(serializers.ModelSerializer):
    """Serializer for ProcessedImage model"""
    
    clothing_type_display = serializers.CharField(source='get_clothing_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    filename = serializers.CharField(source='get_filename', read_only=True)
    is_processing_complete = serializers.BooleanField(read_only=True)
    processing_duration = serializers.DurationField(read_only=True)
    original_image_url = serializers.SerializerMethodField()
    processed_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessedImage
        fields = [
            'id', 'clothing_type', 'clothing_type_display', 'original_image', 'processed_image',
            'status', 'status_display', 'processing_prompt', 'error_message', 'created_at',
            'processed_at', 'openai_response_id', 'gpt4_analysis', 'filename',
            'is_processing_complete', 'processing_duration', 'original_image_url', 'processed_image_url'
        ]
        read_only_fields = ['id', 'created_at', 'processed_at']
    
    def get_original_image_url(self, obj):
        if obj.original_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.original_image.url)
            return obj.original_image.url
        return None
    
    def get_processed_image_url(self, obj):
        if obj.processed_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.processed_image.url)
            return obj.processed_image.url
        return None


class WardrobeItemSerializer(serializers.ModelSerializer):
    """Serializer for WardrobeItem model"""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    color_display = serializers.CharField(source='get_color_display', read_only=True)
    occasion_display = serializers.CharField(source='get_occasion_display', read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)
    original_image_url = serializers.CharField(source='get_original_image_url', read_only=True)
    
    class Meta:
        model = WardrobeItem
        fields = [
            'id', 'processed_image', 'name', 'category', 'category_display', 'color', 'color_display',
            'brand', 'size', 'material', 'occasion', 'occasion_display', 'season', 'style_description',
            'color_palette', 'style_tags', 'is_favorite', 'last_worn', 'wear_count', 'created_at',
            'updated_at', 'image_url', 'original_image_url'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OutfitItemSerializer(serializers.ModelSerializer):
    """Serializer for OutfitItem through model"""
    
    item = WardrobeItemSerializer(read_only=True)
    item_id = serializers.IntegerField(write_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = OutfitItem
        fields = [
            'id', 'outfit', 'item', 'item_id', 'category', 'category_display',
            'match_score', 'style_notes'
        ]


class OutfitRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for OutfitRecommendation model"""
    
    occasion_display = serializers.CharField(source='get_occasion_display', read_only=True)
    outfit_items = OutfitItemSerializer(source='outfititem_set', many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = OutfitRecommendation
        fields = [
            'id', 'name', 'occasion', 'occasion_display', 'season', 'style_description',
            'color_scheme', 'style_tags', 'confidence_score', 'is_favorite', 'rating',
            'last_worn', 'wear_count', 'created_at', 'updated_at', 'outfit_items', 'items_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        return obj.items.count()


class OutfitRecommendationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OutfitRecommendation with items"""
    
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="List of items with their categories and metadata"
    )
    
    class Meta:
        model = OutfitRecommendation
        fields = [
            'name', 'occasion', 'season', 'style_description', 'color_scheme',
            'style_tags', 'confidence_score', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        outfit = OutfitRecommendation.objects.create(**validated_data)
        
        for item_data in items_data:
            item_id = item_data.get('item_id')
            category = item_data.get('category')
            match_score = item_data.get('match_score', 0.0)
            style_notes = item_data.get('style_notes', '')
            
            if item_id and category:
                try:
                    wardrobe_item = WardrobeItem.objects.get(id=item_id)
                    OutfitItem.objects.create(
                        outfit=outfit,
                        item=wardrobe_item,
                        category=category,
                        match_score=match_score,
                        style_notes=style_notes
                    )
                except WardrobeItem.DoesNotExist:
                    continue
        
        return outfit


# Simplified serializers for list views
class ProcessedImageListSerializer(serializers.ModelSerializer):
    """Simplified serializer for ProcessedImage list view"""
    
    clothing_type_display = serializers.CharField(source='get_clothing_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ProcessedImage
        fields = [
            'id', 'clothing_type', 'clothing_type_display', 'status', 'status_display',
            'created_at', 'processed_at'
        ]


class WardrobeItemListSerializer(serializers.ModelSerializer):
    """Simplified serializer for WardrobeItem list view"""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    color_display = serializers.CharField(source='get_color_display', read_only=True)
    
    class Meta:
        model = WardrobeItem
        fields = [
            'id', 'name', 'category', 'category_display', 'color', 'color_display',
            'occasion', 'season', 'is_favorite', 'created_at'
        ]


class OutfitRecommendationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for OutfitRecommendation list view"""
    
    occasion_display = serializers.CharField(source='get_occasion_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = OutfitRecommendation
        fields = [
            'id', 'name', 'occasion', 'occasion_display', 'season', 'confidence_score',
            'is_favorite', 'rating', 'created_at', 'items_count'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()
