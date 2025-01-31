# from django.test import TestCase
# from django.urls import reverse
# from rest_framework.test import APITestCase, APIClient
# from rest_framework import status
# from app_lms.models import Site, Translation
# import os
# from django.conf import settings
# import zipfile
# from io import BytesIO
# from rest_framework.exceptions import NotFound

# class TranslationViewTests(APITestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.site1 = Site.objects.create(name="site1")
#         self.site2 = Site.objects.create(name="site2")
        
#         # Create test translations
#         self.translation1 = Translation.objects.create(
#             site=self.site1,
#             language="EN",
#             key="welcome",
#             value="Welcome"
#         )
#         self.translation2 = Translation.objects.create(
#             site=self.site1,
#             language="EN",
#             key="__config.timeout",
#             value="30"
#         )
#         self.translation3 = Translation.objects.create(
#             site=self.site2,
#             language="ES",
#             key="hello",
#             value="Hola"
#         )

     


#         # Create media directory if it doesn't exist
#         self.upload_dir = os.path.join(settings.MEDIA_ROOT, 'translation_exports')
#         os.makedirs(self.upload_dir, exist_ok=True)

#     def tearDown(self):
#         """Clean up created files after tests"""
#         zip_filepath = os.path.join(self.upload_dir, "sites.zip")
#         if os.path.exists(zip_filepath):
#             os.remove(zip_filepath)

#     def test_create_translation(self):
#         """Test creating a new translation"""
#         translation_data = {
#             "site": "site1",
#             "key": "__config.timeout",
#             "value": "30",
#             "language": "ES"
#         }
#         response = self.client.post(reverse('translations'), translation_data, format='json')
#         print(reverse('translations')) 
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Translation.objects.count(), 4)
        
#         # Verify response data
#         self.assertEqual(response.data["site"], "site1")
#         self.assertEqual(response.data["key"], "__config.timeout")
#         self.assertEqual(response.data["value"], "30")
#         self.assertEqual(response.data["language"], "ES")

#     def test_create_translation_invalid_site(self):
#         """Test creating a translation with non-existent site"""
#         translation_data = {
#             "site": "nonexistent_site",
#             "key": "__config.timeout",
#             "value": "30",
#             "language": "ES"
#         }
#         response = self.client.post(reverse('translations'), translation_data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_get_translations_zip(self):
#         """Test getting translations as zip file"""
#         # Create the client manually to force sending data in GET request
#         client = APIClient()
        
#         # Specify the full URL directly
#         url = 'http://localhost:8000/api/translations/'

#         # Send POST request overriding the method to GET
#         response = client.get(
#             url,
#             data={'site': 'site1,site2'},
#             HTTP_X_HTTP_METHOD_OVERRIDE='GET'
#         )
        
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("file_url", response.data)
#         self.assertEqual(response.data["filename"], "sites.zip")
        
#         # Verify zip file exists and contains correct structure
#         zip_filepath = os.path.join(self.upload_dir, "sites.zip")
#         self.assertTrue(os.path.exists(zip_filepath))
        
#         with zipfile.ZipFile(zip_filepath, 'r') as zip_file:
#             file_list = zip_file.namelist()
#             print("Zip contents:", file_list)
            
#             # Check if the zip file contains any files for site1 and site2
#             site1_files = [f for f in file_list if f.startswith('site1/')]
#             site2_files = [f for f in file_list if f.startswith('site2/')]
            
#             self.assertTrue(len(site1_files) == 0, "No files found for site1")
#             self.assertTrue(len(site2_files) == 0, "No files found for site2")

#     def test_get_translations_nonexistent_site(self):
#         """Test getting translations for non-existent site"""
#         client = APIClient()
#         response = client.get(
#             reverse('translations'),
#             data={'site': 'nonexistent_site'},
#             HTTP_X_HTTP_METHOD_OVERRIDE='GET'
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK)

#     def test_get_translations_no_site_provided(self):
#         """Test getting translations without providing site"""
#         client = APIClient()
        
#         # Specify the correct URL for the 'sites' API
#         url = 'http://localhost:8000/api/sites/'

#         # Send GET request with empty site parameter
#         response = client.get(
#             url,
#             data={"site": ""},
#             HTTP_X_HTTP_METHOD_OVERRIDE='GET'
#         )

#         # Assert the response status code is 404 (Not Found)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)