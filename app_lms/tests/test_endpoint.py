from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from app_lms.models import Site, Translation
import os
from django.conf import settings
import zipfile
import json
from datetime import datetime

class SiteViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.site_data = {"name": "testsite", "description": "Test Site Description"}
        self.site = Site.objects.create(name="existing_site", description="Existing Site")

    def test_create_site(self):
        """Test creating a new site"""
        response = self.client.post(reverse('site-list'), self.site_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Site.objects.count(), 2)
        self.assertEqual(Site.objects.get(name="testsite").description, "Test Site Description")

    def test_create_duplicate_site(self):
        """Test creating a site with duplicate name"""
        duplicate_data = {"name": "existing_site", "description": "Duplicate Site"}
        response = self.client.post(reverse('site-list'), duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_sites(self):
        """Test getting list of sites"""
        response = self.client.get(reverse('site-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class TranslationViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.site1 = Site.objects.create(name="site1", description="Site 1")
        self.site2 = Site.objects.create(name="site2", description="Site 2")
        
        # Create test translations
        self.translation1 = Translation.objects.create(
            site=self.site1,
            language="EN",
            key_type="TPL",
            key="welcome",
            value="Welcome"
        )
        self.translation2 = Translation.objects.create(
            site=self.site1,
            language="EN",
            key_type="INI",
            key="goodbye",
            value="Goodbye"
        )
        self.translation3 = Translation.objects.create(
            site=self.site2,
            language="EN",
            key_type="TPL",
            key="hello",
            value="Hello"
        )

        # Create media directory if it doesn't exist
        self.upload_dir = os.path.join(settings.MEDIA_ROOT, 'translation_exports')
        os.makedirs(self.upload_dir, exist_ok=True)

    def tearDown(self):
        """Clean up created files after tests"""
        zip_filepath = os.path.join(self.upload_dir, "sites.zip")
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)

    def test_create_translation(self):
        """Test creating a new translation"""
        translation_data = {
            "site": self.site1.id,
            "language": "FR",
            "key_type": "TPL",
            "key": "welcome",
            "value": "Bienvenue"
        }
        response = self.client.post(reverse('translation-list'), translation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Translation.objects.count(), 4)

    def test_get_translations_zip(self):
        """Test getting translations as zip file"""
        data = {"site": "site1,site2"}
        response = self.client.get(reverse('translation-list'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("file_url", response.data)
        self.assertEqual(response.data["filename"], "sites.zip")
        
        # Verify zip file exists and contains correct structure
        zip_filepath = os.path.join(self.upload_dir, "sites.zip")
        self.assertTrue(os.path.exists(zip_filepath))
        
        with zipfile.ZipFile(zip_filepath, 'r') as zip_file:
            file_list = zip_file.namelist()
            
            # Check if expected files exist
            self.assertIn("site1/en-EN.tpl", file_list)
            self.assertIn("site1/en-EN.ini", file_list)
            self.assertIn("site2/en-EN.tpl", file_list)
            
            # Check content of one file
            content = zip_file.read("site1/en-EN.tpl").decode('utf-8')
            self.assertIn("# Site: site1", content)
            self.assertIn("welcome=Welcome", content)

    def test_get_translations_nonexistent_site(self):
        """Test getting translations for non-existent site"""
        data = {"site": "nonexistent_site"}
        response = self.client.get(reverse('translation-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should still return 200 as it skips non-existent sites

    def test_get_translations_no_site_provided(self):
        """Test getting translations without providing site"""
        data = {"site": ""}
        response = self.client.get(reverse('translation-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_translations_file_content(self):
        """Test the content of generated translation files"""
        data = {"site": "site1"}
        response = self.client.get(reverse('translation-list'), data, format='json')
        
        zip_filepath = os.path.join(self.upload_dir, "sites.zip")
        with zipfile.ZipFile(zip_filepath, 'r') as zip_file:
            # Check TPL file content
            tpl_content = zip_file.read("site1/en-EN.tpl").decode('utf-8')
            self.assertIn("# Site: site1", tpl_content)
            self.assertIn("# Language: en-EN", tpl_content)
            self.assertIn("# Total Keys: 1", tpl_content)
            self.assertIn("welcome=Welcome", tpl_content)
            
            # Check INI file content
            ini_content = zip_file.read("site1/en-EN.ini").decode('utf-8')
            self.assertIn("# Site: site1", ini_content)
            self.assertIn("# Language: en-EN", ini_content)
            self.assertIn("# Total Keys: 1", ini_content)
            self.assertIn("goodbye=Goodbye", ini_content)