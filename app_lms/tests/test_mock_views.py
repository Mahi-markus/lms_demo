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
from unittest.mock import patch, MagicMock , Mock
from app_lms.serializers import TranslationSerializer ,SiteSerializer



class SiteViewTests(APITestCase):
    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()
        self.sites_url = reverse('sites')  # Assuming 'sites' is your URL name
        
        # Create some test sites
        self.site1 = Site.objects.create(name="test_site_1")
        self.site2 = Site.objects.create(name="test_site_2")

    def tearDown(self):
        """Clean up after tests"""
        Site.objects.all().delete()

    def test_create_site_success(self):
        """Test successful site creation"""
        site_data = {"name": "new_test_site"}
        
        response = self.client.post(self.sites_url, site_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], site_data['name'])
        self.assertTrue(Site.objects.filter(name=site_data['name']).exists())

    def test_create_site_invalid_data(self):
        """Test site creation with invalid data"""
        # Empty name
        invalid_data = {"name": ""}
        
        response = self.client.post(self.sites_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_create_duplicate_site(self):
        """Test creating a site with a name that already exists"""
        duplicate_data = {"name": "test_site_1"}  # Same as site1 created in setUp
        
        response = self.client.post(self.sites_url, duplicate_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    @patch('app_lms.models.Site.objects.all')
    def test_get_sites_success(self, mock_sites):
        """Test successful retrieval of all sites"""
        # Set up mock return value
        mock_sites.return_value = [self.site1, self.site2]
        
        response = self.client.get(self.sites_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'test_site_1')
        self.assertEqual(response.data[1]['name'], 'test_site_2')

    @patch('app_lms.models.Site.objects.all')
    def test_get_sites_empty(self, mock_sites):
        """Test getting sites when no sites exist"""
        # Set up mock to return empty queryset
        mock_sites.return_value = Site.objects.none()
        
        response = self.client.get(self.sites_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self.assertEqual(response.data, [])

    # @patch('app_lms.serializers.SiteSerializer.is_valid')
    # def test_create_site_serializer_validation_error(self, mock_is_valid):
    #     """Test handling of serializer validation errors"""
    #     mock_is_valid.return_value = False
    #     site_data = {"name": "invalid_site"}
        
    #     response = self.client.post(self.sites_url, site_data, format='json')
        
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # @patch('app_lms.models.Site.objects.all')
    # def test_get_sites_database_error(self, mock_sites):
    #     """Test handling of database errors during site retrieval"""
    #     # Simulate database error
    #     mock_sites.side_effect = Exception("Database error")
        
    #     response = self.client.get(self.sites_url)
        
    #     # Since we don't have explicit error handling in the view,
    #     # this should raise a 500 error
    #     self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)



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

	@patch('app_lms.models.Translation.objects.filter') # Mock the filter method
	def test_get_translations_zip(self, mock_get_queryset):
		"""Test getting translations as a zip file using a mock API"""
		
		# Create a mock queryset with fake Translation objects
		mock_translation1 = Mock(spec=Translation)
		mock_translation2 = Mock(spec=Translation)
		mock_queryset = MagicMock()
		mock_queryset.all.return_value = [mock_translation1, mock_translation2]
		
		# Mock the filter method to return the fake queryset
		mock_get_queryset.return_value = mock_queryset

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
    
	