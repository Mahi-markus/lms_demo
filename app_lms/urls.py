from django.urls import path
from .views import TranslationView, SiteView

urlpatterns = [
    path('sites/', SiteView.as_view(), name='sites'),
    path('translations/', TranslationView.as_view(), name='translations'),
]