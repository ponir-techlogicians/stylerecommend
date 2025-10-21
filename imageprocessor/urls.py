from django.urls import path
from . import views

app_name = 'imageprocessor'

urlpatterns = [
    # Image processing URLs
    path('', views.ImageUploadView.as_view(), name='upload'),
    path('result/<int:image_id>/', views.ImageResultView.as_view(), name='result'),
    path('gallery/', views.ImageListView.as_view(), name='list'),
    path('detail/<int:image_id>/', views.ImageDetailView.as_view(), name='detail'),
    path('api/status/<int:image_id>/', views.check_processing_status, name='status'),
    
    # Wardrobe management URLs
    path('wardrobe/', views.WardrobeListView.as_view(), name='wardrobe_list'),
    path('wardrobe/item/<int:item_id>/', views.WardrobeItemDetailView.as_view(), name='wardrobe_item_detail'),
    path('wardrobe/item/<int:item_id>/edit/', views.WardrobeItemEditView.as_view(), name='wardrobe_item_edit'),
    path('convert/<int:image_id>/', views.ConvertToWardrobeView.as_view(), name='convert_to_wardrobe'),
    
    # Outfit recommendation URLs
    path('outfits/', views.OutfitRecommendationView.as_view(), name='outfit_recommendations'),
    path('outfits/saved/', views.SavedOutfitsView.as_view(), name='saved_outfits'),
    path('outfits/<int:outfit_id>/', views.OutfitDetailView.as_view(), name='outfit_detail'),
    
    # AJAX URLs
    path('api/toggle-favorite/<int:item_id>/', views.toggle_favorite_item, name='toggle_favorite_item'),
    path('api/analyze-item/<int:item_id>/', views.analyze_wardrobe_item, name='analyze_wardrobe_item'),
    path('api/rate-outfit/<int:outfit_id>/', views.rate_outfit, name='rate_outfit'),

    # Accounts
    path('accounts/register/', views.register, name='register'),
]
