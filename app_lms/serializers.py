from rest_framework import serializers
from .models import Site, Translation

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['id', 'name']

class TranslationSerializer(serializers.ModelSerializer):
    site = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Site.objects.all()
    )
    
    class Meta:
        model = Translation
        fields = ['site', 'key', 'value', 'language']
        
    def validate_key(self, value):
        if not (value.startswith('//') or value.startswith('__')):
            raise serializers.ValidationError(
                "Key must start with '//' for TPL type or '__' for INI type"
            )
        return value
