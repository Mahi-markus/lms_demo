from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from .models import Site, Translation
from .serializers import TranslationSerializer,SiteSerializer
import io
import zipfile
from datetime import datetime
from django.conf import settings
import os



class SiteView(APIView):
    def post(self, request):
        serializer = SiteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        sites = Site.objects.all()
        serializer = SiteSerializer(sites, many=True)
        return Response(serializer.data)

class TranslationView(APIView):
    def post(self, request):
        serializer = TranslationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        try:
            # Split the sites string into a list
            site_names = request.data.get('site', '').split(',')
            # if not site_names:
            #     return Response({"error": "No sites provided"}, status=status.HTTP_404_NOT_FOUND)

            # Create directory for storing zip files if it doesn't exist
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'translation_exports')
            os.makedirs(upload_dir, exist_ok=True)

            # Generate zip filename
            zip_filename = "sites.zip"
            zip_filepath = os.path.join(upload_dir, zip_filename)

            # Create zip file in the directory
            with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
                for site_name in site_names:
                    site_name = site_name.strip()
                    try:
                        site = Site.objects.get(name=site_name)
                        translations = Translation.objects.filter(site=site)
                        
                        if not translations.exists():
                            continue

                        # Group translations by language and key_type
                        language_files = {}  # Structure: {'EN': {'TPL': {...}, 'INI': {...}}}
                        for trans in translations:
                            lang = trans.language
                            if lang not in language_files:
                                language_files[lang] = {'TPL': {}, 'INI': {}}
                            file_type = 'TPL' if trans.key_type == 'TPL' else 'INI'
                            language_files[lang][file_type][trans.key] = trans.value

                        # Create files for each language under site-specific folder
                        for lang, type_contents in language_files.items():
                            # Convert language code to locale format
                            locale = f"{lang.lower()}-{lang.upper()}"
                            
                            # Create metadata header
                            metadata = (
                                f"# Site: {site_name}\n"
                                f"# Language: {locale}\n"
                                f"# Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                f"# Total Keys: {{key_count}}\n"
                                "# Format: key=value\n"
                                "#\n\n"
                            )
                            
                            # Create TPL file if content exists
                            if type_contents['TPL']:
                                tpl_content = metadata.format(key_count=len(type_contents['TPL']))
                                for key, value in type_contents['TPL'].items():
                                    tpl_content += f"# Key: {key}\n"
                                    tpl_content += f"{key}={value}\n\n"
                                zip_file.writestr(f"{site_name}/{locale}.tpl", tpl_content)

                            # Create INI file if content exists
                            if type_contents['INI']:
                                ini_content = metadata.format(key_count=len(type_contents['INI']))
                                for key, value in type_contents['INI'].items():
                                    ini_content += f"# Key: {key}\n"
                                    ini_content += f"{key}={value}\n\n"
                                zip_file.writestr(f"{site_name}/{locale}.ini", ini_content)

                    except Site.DoesNotExist:
                        continue  # Skip if site doesn't exist and continue with next site

            # Get the relative path for the file URL
            relative_path = os.path.relpath(zip_filepath, settings.MEDIA_ROOT)
            file_url = os.path.join(settings.MEDIA_URL, relative_path)

            return Response({
                "message": "Translation files generated successfully",
                "file_url": file_url,
                "filename": zip_filename
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

