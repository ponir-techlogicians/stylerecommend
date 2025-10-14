from django import forms
from django.core.exceptions import ValidationError
from .models import ProcessedImage, WardrobeItem, OutfitRecommendation


class WardrobeItemForm(forms.ModelForm):
    """Form for creating and editing wardrobe items"""
    
    class Meta:
        model = WardrobeItem
        fields = [
            'name', 'category', 'color', 'brand', 'size', 'material',
            'occasion', 'season', 'is_favorite'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a name for this item'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brand name (optional)'
            }),
            'size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Size (optional)'
            }),
            'material': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Material/fabric (optional)'
            }),
            'occasion': forms.Select(attrs={'class': 'form-select'}),
            'season': forms.Select(attrs={'class': 'form-select'}),
            'is_favorite': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make some fields optional
        self.fields['brand'].required = False
        self.fields['size'].required = False
        self.fields['material'].required = False


class OutfitRecommendationForm(forms.ModelForm):
    """Form for creating and editing outfit recommendations"""
    
    class Meta:
        model = OutfitRecommendation
        fields = [
            'name', 'occasion', 'season', 'is_favorite', 'rating'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a name for this outfit'
            }),
            'occasion': forms.Select(attrs={'class': 'form-select'}),
            'season': forms.Select(attrs={'class': 'form-select'}),
            'is_favorite': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'placeholder': 'Rate 1-5'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].required = False


class OutfitSearchForm(forms.Form):
    """Form for searching outfit recommendations"""
    
    OCCASION_CHOICES = [
        ('', 'Any Occasion'),
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
        ('', 'Any Season'),
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall'),
        ('winter', 'Winter'),
        ('all', 'All Season'),
    ]
    
    occasion = forms.ChoiceField(
        choices=OCCASION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    season = forms.ChoiceField(
        choices=SEASON_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    max_outfits = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Number of outfits to generate'
        })
    )


class WardrobeItemSearchForm(forms.Form):
    """Form for searching wardrobe items"""
    
    CATEGORY_CHOICES = [
        ('', 'All Categories'),
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('shoes', 'Shoes'),
        ('accessories', 'Accessories'),
        ('outerwear', 'Outerwear'),
        ('dress', 'Dress'),
    ]
    
    COLOR_CHOICES = [
        ('', 'All Colors'),
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
        ('', 'All Occasions'),
        ('casual', 'Casual'),
        ('formal', 'Formal'),
        ('business', 'Business'),
        ('party', 'Party'),
        ('sport', 'Sport'),
        ('evening', 'Evening'),
        ('weekend', 'Weekend'),
        ('travel', 'Travel'),
    ]
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    color = forms.ChoiceField(
        choices=COLOR_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    occasion = forms.ChoiceField(
        choices=OCCASION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, brand, or material...'
        })
    )
    
    favorites_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ConvertToWardrobeForm(forms.Form):
    """Form for converting processed images to wardrobe items"""
    
    processed_image = forms.ModelChoiceField(
        queryset=ProcessedImage.objects.filter(status='completed'),
        widget=forms.HiddenInput()
    )
    
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a name for this item'
        })
    )
    
    category = forms.ChoiceField(
        choices=WardrobeItem.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    color = forms.ChoiceField(
        choices=WardrobeItem.COLOR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    brand = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brand name (optional)'
        })
    )
    
    size = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Size (optional)'
        })
    )
    
    material = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Material/fabric (optional)'
        })
    )
    
    occasion = forms.ChoiceField(
        choices=WardrobeItem.OCCASION_CHOICES,
        initial='casual',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    season = forms.ChoiceField(
        choices=[
            ('spring', 'Spring'),
            ('summer', 'Summer'),
            ('fall', 'Fall'),
            ('winter', 'Winter'),
            ('all', 'All Season')
        ],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean_processed_image(self):
        """Validate that the processed image is completed"""
        processed_image = self.cleaned_data['processed_image']
        if processed_image.status != 'completed':
            raise ValidationError('Only completed processed images can be added to wardrobe.')
        return processed_image
