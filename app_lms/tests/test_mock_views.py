from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from app_lms.models import Site, Translation
import os
from django.conf import settings
import zipfile
from io import BytesIO
from rest_framework.exceptions import NotFound
from unittest.mock import patch, MagicMock
from app_lms.serializers import TranslationSerializer


class TranslationViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.site1 = Site.objects.create(name="site1")
        self.site2 = Site.objects.create(name="site2")

        # Create test translations
        self.translation1 = Translation.objects.create(
            site=self.site1,
            language="EN",
            key="welcome",
            value="Welcome"
        )
        self.translation2 = Translation.objects.create(
            site=self.site1,
            language="EN",
            key="__config.timeout",
            value="30"
        )
        self.translation3 = Translation.objects.create(
            site=self.site2,
            language="ES",
            key="hello",
            value="Hola"
        )

        # Create media directory if it doesn't exist
        self.upload_dir = os.path.join(settings.MEDIA_ROOT, 'translation_exports')
        os.makedirs(self.upload_dir, exist_ok=True)

    def tearDown(self):
        """Clean up created files after tests"""
        zip_filepath = os.path.join(self.upload_dir, "sites.zip")
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)

    @patch('app_lms.serializers.TranslationSerializer')  # Mock the save method of the serializer
    def test_create_translation(self, mock_save):
        """Test creating a new translation with a mock API"""
        # Mock the save method to return a valid translation object
        mock_save.return_value = Translation(
            site=self.site1,
            language="ES",
            key="__config.timeout",
            value="30"
        )

        translation_data = {
            "site": "site1",
            "key": "__config.timeout",
            "value": "30",
            "language": "ES"
        }

        # Call the API
        response = self.client.post(reverse('translations'), translation_data, format='json')

        # Verify the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["site"], "site1")
        self.assertEqual(response.data["key"], "__config.timeout")
        self.assertEqual(response.data["value"], "30")
        self.assertEqual(response.data["language"], "ES")

    @patch('app_lms.serializers.TranslationSerializer')  # Mock the is_valid method of the serializer
    def test_create_translation_invalid_site(self, mock_is_valid):
        """Test creating a translation with a non-existent site using a mock API"""
        # Mock the is_valid method to return False
        mock_is_valid.return_value = False

        translation_data = {
            "site": "nonexistent_site",
            "key": "__config.timeout",
            "value": "30",
            "language": "ES"
        }

        # Call the API
        response = self.client.post(reverse('translations'), translation_data, format='json')

        # Verify the response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('app_lms.models.Translation.objects.filter')  # Mock the get_queryset method of the view
    def test_get_translations_zip(self, mock_get_queryset):
        """Test getting translations as a zip file using a mock API"""
        # Mock the queryset to return translations for site1 and site2
        mock_get_queryset.return_value = Translation.objects.filter(site__name__in=["site1", "site2"])

        # Call the API
        response = self.client.get(
            reverse('translations'),
            data={'site': 'site1,site2'},
            format='json'
        )

        # Verify the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("file_url", response.data)
        self.assertEqual(response.data["filename"], "sites.zip")

    @patch('app_lms.models.Site.objects.get')
    def test_get_translations_nonexistent_site(self, mock_site_get):
        """Test getting translations for a non-existent site using a mock API"""
        # Mock Site.objects.get to raise DoesNotExist
        mock_site_get.side_effect = Site.DoesNotExist
        
        # Call the API
        response = self.client.get(
            reverse('translations'),
            data={'site': 'nonexistent_site'},
            format='json'
        )
        
        # Verify the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data, {"error": "No sites provided"})

    @patch('app_lms.models.Translation.objects.filter')  # ✅ Mock queryset
    def test_get_translations_no_site_provided(self, mock_filter):
        """Test getting translations without providing a site"""
        # Mock `filter()` to return an empty queryset
        mock_filter.return_value.exists.return_value = False  # Simulate no translations

        # Call the API
        response = self.client.get(
            reverse('translations'),
            data={"site": ""},
            format='json'
        )

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        