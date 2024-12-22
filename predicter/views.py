import os
import uuid
import ffmpeg

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from .models import Media, Application
from .services import frames_extraction, predict_video

@login_required
def predict_view(request):
    user_uploaded_media = Media.objects.filter(user=request.user).order_by('-created_at')
    for media in user_uploaded_media:
        media.result_slug = media.result.lower().replace(' ', '_')
    context = {
        "uploaded_media": user_uploaded_media
    }

    """
    Process uploaded file
    1. Generate a random UUID v4 file name for the file.
    2. Save the file in chunk to the local file system.
    3. Save the file data in database.
    """
    if request.method == 'POST' and request.FILES.get('file-upload'):
        uploaded_file = request.FILES['file-upload']

        # * Generate unique file name
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        try:
            save_path = os.path.join(settings.MEDIA_ROOT, 'uploads', unique_filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # * Save file to /media/uploads location
            with open(save_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # * Extract video metadata
            metadata = ffmpeg.probe(save_path)
            duration = float(metadata['format']['duration'])  # Duration in seconds
            video_stream = next((stream for stream in metadata['streams'] if stream['codec_type'] == 'video'), None)
            resolution = f"{video_stream['width']}x{video_stream['height']}" if video_stream else "Unknown"

            # * Use service to predict video
            response = predict_video(save_path)

            # * Save file data into database
            Media.objects.create(
                name=unique_filename,
                original_name=uploaded_file.name,
                local_path=f'{settings.MEDIA_URL}uploads/{unique_filename}',
                size_byte=uploaded_file.size,
                duration=duration,
                resolution=resolution,
                result="Non Violence" if response.get("predicted_class") == "NonViolence" else "Violence",
                user=request.user
            )

            user_uploaded_media = Media.objects.filter(user=request.user).order_by('-created_at')
            for media in user_uploaded_media:
                media.result_slug = media.result.lower().replace(' ', '_')
            context = {
                "status": "success",
                "message": "File uploaded successfully!",
                "uploaded_media": user_uploaded_media
            }
            print("bug:", user_uploaded_media)
        except Exception as e:
            context = {"status": "error", "message": str(e)}

    return render(request, 'predict.html', context=context)

@login_required
def applications_view(request):
    applications = Application.objects.all().order_by('-created_at')
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'application.html', context={'applications': page_obj})


def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048  # Key size in bits
    )

    # Serialize the private key to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # Generate public key
    public_key = private_key.public_key()

    # Serialize the public key to PEM format
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return public_key_pem, private_key_pem

@login_required
def create_application(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        if name and description:
            public_key, private_key = generate_rsa_key_pair()

            Application.objects.create(
                name=name,
                description=description,
                status='active',
                public_key=public_key,
                private_key=private_key,
                created_at=timezone.now(),
                user=request.user
            )
            messages.success(request, "Application created successfully.")
        else:
            messages.error(request, "Both name and description are required.")

    return redirect('/services/applications/')

def application_detail(request, id):
    application = Application.objects.get(id=id)
    return render(request, 'application-detail.html', context={'application': application})
