from django.contrib import admin
from .models import ProcessedImage


@admin.register(ProcessedImage)
class ProcessedImageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'clothing_type', 'status', 'created_at', 
        'processed_at', 'get_filename', 'is_processing_complete'
    ]
    list_filter = ['clothing_type', 'status', 'created_at']
    search_fields = ['clothing_type', 'original_image']
    readonly_fields = [
        'created_at', 'processed_at', 'openai_response_id', 
        'processing_prompt', 'get_processing_duration'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('clothing_type', 'original_image', 'processed_image')
        }),
        ('Processing Status', {
            'fields': ('status', 'error_message', 'openai_response_id')
        }),
        ('Processing Details', {
            'fields': ('processing_prompt', 'gpt4_analysis', 'get_processing_duration'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_processing_duration(self, obj):
        """Display processing duration"""
        duration = obj.get_processing_duration()
        if duration:
            return f"{duration.total_seconds():.1f} seconds"
        return "N/A"
    get_processing_duration.short_description = "Processing Duration"
    
    def get_filename(self, obj):
        """Display original filename"""
        return obj.get_filename()
    get_filename.short_description = "Filename"