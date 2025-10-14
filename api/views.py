from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Avg

from imageprocessor.models import ProcessedImage, WardrobeItem, OutfitRecommendation, OutfitItem
from .serializers import (
    ProcessedImageSerializer, ProcessedImageListSerializer,
    WardrobeItemSerializer, WardrobeItemListSerializer,
    OutfitRecommendationSerializer, OutfitRecommendationListSerializer,
    OutfitRecommendationCreateSerializer, OutfitItemSerializer
)


class ProcessedImageViewSet(viewsets.ModelViewSet):
    """ViewSet for ProcessedImage model"""
    
    queryset = ProcessedImage.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['clothing_type', 'status']
    search_fields = ['processing_prompt', 'gpt4_analysis']
    ordering_fields = ['created_at', 'processed_at', 'clothing_type']
    ordering = ['-created_at']
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessedImageListSerializer
        return ProcessedImageSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by processing status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by clothing type
        clothing_type = self.request.query_params.get('clothing_type')
        if clothing_type:
            queryset = queryset.filter(clothing_type=clothing_type)
        
        # Filter completed processing
        completed_only = self.request.query_params.get('completed_only')
        if completed_only and completed_only.lower() == 'true':
            queryset = queryset.filter(status='completed')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Reprocess an image"""
        processed_image = self.get_object()
        
        # Reset status to pending for reprocessing
        processed_image.status = 'pending'
        processed_image.error_message = None
        processed_image.save()
        
        return Response({
            'message': 'Image marked for reprocessing',
            'status': processed_image.status
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get processing statistics"""
        total = ProcessedImage.objects.count()
        pending = ProcessedImage.objects.filter(status='pending').count()
        processing = ProcessedImage.objects.filter(status='processing').count()
        completed = ProcessedImage.objects.filter(status='completed').count()
        failed = ProcessedImage.objects.filter(status='failed').count()
        
        return Response({
            'total': total,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed
        })


class WardrobeItemViewSet(viewsets.ModelViewSet):
    """ViewSet for WardrobeItem model"""
    
    queryset = WardrobeItem.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'color', 'occasion', 'season', 'is_favorite']
    search_fields = ['name', 'brand', 'material', 'style_description']
    ordering_fields = ['name', 'created_at', 'wear_count', 'last_worn']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WardrobeItemListSerializer
        return WardrobeItemSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by color
        color = self.request.query_params.get('color')
        if color:
            queryset = queryset.filter(color=color)
        
        # Filter by occasion
        occasion = self.request.query_params.get('occasion')
        if occasion:
            queryset = queryset.filter(occasion=occasion)
        
        # Filter favorites only
        favorites_only = self.request.query_params.get('favorites_only')
        if favorites_only and favorites_only.lower() == 'true':
            queryset = queryset.filter(is_favorite=True)
        
        # Filter by season
        season = self.request.query_params.get('season')
        if season:
            queryset = queryset.filter(season__in=[season, 'all'])
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status"""
        item = self.get_object()
        item.is_favorite = not item.is_favorite
        item.save()
        
        return Response({
            'id': item.id,
            'is_favorite': item.is_favorite
        })
    
    @action(detail=True, methods=['post'])
    def mark_worn(self, request, pk=None):
        """Mark item as worn"""
        item = self.get_object()
        item.wear_count += 1
        item.save()
        
        return Response({
            'id': item.id,
            'wear_count': item.wear_count
        })
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available categories with counts"""
        categories = []
        for choice in WardrobeItem.CATEGORY_CHOICES:
            count = WardrobeItem.objects.filter(category=choice[0]).count()
            categories.append({
                'value': choice[0],
                'label': choice[1],
                'count': count
            })
        
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def colors(self, request):
        """Get available colors with counts"""
        colors = []
        for choice in WardrobeItem.COLOR_CHOICES:
            count = WardrobeItem.objects.filter(color=choice[0]).count()
            colors.append({
                'value': choice[0],
                'label': choice[1],
                'count': count
            })
        
        return Response(colors)


class OutfitRecommendationViewSet(viewsets.ModelViewSet):
    """ViewSet for OutfitRecommendation model"""
    
    queryset = OutfitRecommendation.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['occasion', 'season', 'is_favorite']
    search_fields = ['name', 'style_description']
    ordering_fields = ['name', 'created_at', 'confidence_score', 'rating']
    ordering = ['-confidence_score', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OutfitRecommendationCreateSerializer
        elif self.action == 'list':
            return OutfitRecommendationListSerializer
        return OutfitRecommendationSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by occasion
        occasion = self.request.query_params.get('occasion')
        if occasion:
            queryset = queryset.filter(occasion=occasion)
        
        # Filter by season
        season = self.request.query_params.get('season')
        if season:
            queryset = queryset.filter(season__in=[season, 'all'])
        
        # Filter favorites only
        favorites_only = self.request.query_params.get('favorites_only')
        if favorites_only and favorites_only.lower() == 'true':
            queryset = queryset.filter(is_favorite=True)
        
        # Filter by minimum confidence score
        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            try:
                min_confidence = float(min_confidence)
                queryset = queryset.filter(confidence_score__gte=min_confidence)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status"""
        outfit = self.get_object()
        outfit.is_favorite = not outfit.is_favorite
        outfit.save()
        
        return Response({
            'id': outfit.id,
            'is_favorite': outfit.is_favorite
        })
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate an outfit (1-5)"""
        outfit = self.get_object()
        rating = request.data.get('rating')
        
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return Response(
                {'error': 'Rating must be an integer between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        outfit.rating = rating
        outfit.save()
        
        return Response({
            'id': outfit.id,
            'rating': outfit.rating
        })
    
    @action(detail=True, methods=['post'])
    def mark_worn(self, request, pk=None):
        """Mark outfit as worn"""
        outfit = self.get_object()
        outfit.wear_count += 1
        outfit.save()
        
        # Also increment wear count for all items in the outfit
        for item in outfit.items.all():
            item.wear_count += 1
            item.save()
        
        return Response({
            'id': outfit.id,
            'wear_count': outfit.wear_count
        })
    
    @action(detail=False, methods=['get'])
    def recommend(self, request):
        """Get outfit recommendations based on criteria"""
        occasion = request.query_params.get('occasion')
        season = request.query_params.get('season')
        category = request.query_params.get('category')
        
        queryset = self.get_queryset()
        
        if occasion:
            queryset = queryset.filter(occasion=occasion)
        
        if season:
            queryset = queryset.filter(season__in=[season, 'all'])
        
        # Filter by items that have specific category
        if category:
            queryset = queryset.filter(items__category=category).distinct()
        
        # Order by confidence score and limit results
        queryset = queryset.order_by('-confidence_score')[:10]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get outfit statistics"""
        total = OutfitRecommendation.objects.count()
        favorites = OutfitRecommendation.objects.filter(is_favorite=True).count()
        rated = OutfitRecommendation.objects.exclude(rating__isnull=True).count()
        
        # Average rating
        avg_rating = OutfitRecommendation.objects.exclude(rating__isnull=True).aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0
        
        # Most worn outfit
        most_worn = OutfitRecommendation.objects.order_by('-wear_count').first()
        
        return Response({
            'total': total,
            'favorites': favorites,
            'rated': rated,
            'average_rating': round(avg_rating, 2),
            'most_worn': {
                'id': most_worn.id,
                'name': most_worn.name,
                'wear_count': most_worn.wear_count
            } if most_worn else None
        })


class OutfitItemViewSet(viewsets.ModelViewSet):
    """ViewSet for OutfitItem through model"""
    
    queryset = OutfitItem.objects.all()
    serializer_class = OutfitItemSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['outfit', 'item', 'category']
    ordering_fields = ['match_score', 'category']
    ordering = ['category', '-match_score']