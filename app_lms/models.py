
# Create your models here.
from django.db import models

class Site(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Translation(models.Model):
    LANGUAGE_CHOICES = [
        ('EN', 'US'),
        ('ES', 'ES'),
    ]
    
    KEY_TYPE_CHOICES = [
        ('TPL', 'Template'),
        ('INI', 'Initialize'),
    ]
    
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='translations')
    key = models.CharField(max_length=255)
    value = models.TextField()
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    key_type = models.CharField(max_length=3, choices=KEY_TYPE_CHOICES)
    
    class Meta:
        unique_together = ('site', 'key', 'language')
    
    def save(self, *args, **kwargs):
        # Automatically determine key_type based on key prefix
        if self.key.startswith('//'):
            self.key_type = 'TPL'
        elif self.key.startswith('__'):
            self.key_type = 'INI'
        super().save(*args, **kwargs)