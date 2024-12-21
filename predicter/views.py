import os
import uuid
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Media
import ffmpeg

@login_required
def predict_view(request):
    user_uploaded_media = Media.objects.filter(user=request.user)
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

            # * Save file data into database
            Media.objects.create(
                name=unique_filename,
                original_name=uploaded_file.name,
                local_path=f'{settings.MEDIA_URL}uploads/{unique_filename}',
                size_bytes=uploaded_file.size,
                duration=duration,
                resolution=resolution,
                user=request.user
            )

            user_uploaded_media = Media.objects.filter(user=request.user)
            context = {
                "status": "success",
                "message": "File uploaded successfully!",
                "uploaded_media": user_uploaded_media
            }
        except Exception as e:
            context = {"status": "error", "message": str(e)}

    return render(request, 'predict.html', context=context)

@login_required
def applications_view(request):
    print("called applications_view")
    return render(request, 'application.html')