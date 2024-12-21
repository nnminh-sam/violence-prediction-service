import os
import uuid
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def predict_view(request):
    """
    Process uploaded file
    - Generate a random UUID v4 file name for the file before saving it.
    """
    if request.method == 'POST' and request.FILES.get('file-upload'):
        uploaded_file = request.FILES['file-upload']

        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        save_path = os.path.join(settings.MEDIA_ROOT, 'uploads', unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save file to /media/uploads location
        with open(save_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Add a flag for success in the context
        return render(request, 'predict.html', context={"status": "success", "message": "File uploaded successfully!"})

    return render(request, 'predict.html')

@login_required
def applications_view(request):
    print("called applications_view")
    return render(request, 'application.html')