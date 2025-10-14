from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'processed-images', views.ProcessedImageViewSet)
router.register(r'wardrobe-items', views.WardrobeItemViewSet)
router.register(r'outfit-recommendations', views.OutfitRecommendationViewSet)
router.register(r'outfit-items', views.OutfitItemViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
