import os
import uuid
import ffmpeg

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from django.views.decorators.csrf import csrf_exempt

from .models import Media, Application
from .services import frames_extraction, predict_video


def media_process(file, user, application):
    """
    Process uploaded file
    1. Generate a random UUID v4 file name for the file.
    2. Save the file in chunk to the local file system.
    3. Save the file data in database.
    """

    file_extension = os.path.splitext(file.name)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    try:
        save_path = os.path.join(settings.MEDIA_ROOT, 'uploads', unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        metadata = ffmpeg.probe(save_path)
        duration = float(metadata['format']['duration'])  # Duration in seconds
        video_stream = next((stream for stream in metadata['streams'] if stream['codec_type'] == 'video'), None)
        resolution = f"{video_stream['width']}x{video_stream['height']}" if video_stream else "Unknown"

        response = predict_video(save_path)

        created_media = Media.objects.create(
            name=unique_filename,
            original_name=file.name,
            local_path=f'{settings.MEDIA_URL}uploads/{unique_filename}',
            size_byte=file.size,
            duration=duration,
            resolution=resolution,
            result="Non Violence" if response.get("predicted_class") == "NonViolence" else "Violence",
            user=user,
            application=application,
        )
        return (
            None,
            {
                "media_id": created_media.id,
                "media_name": created_media.name,
                "predicted_class": response.get("predicted_class"),
                "predicted_confidence": response.get("confidence"),
            }
        )
    except Exception as e:
        return e, None


@login_required
def predict_view(request):
    user_uploaded_media = Media.objects.filter(
        user=request.user,
        application_id__isnull=True
    ).order_by('-created_at')
    for media in user_uploaded_media:
        media.result_slug = media.result.lower().replace(' ', '_')
    context = {
        "uploaded_media": user_uploaded_media
    }

    if request.method == 'POST' and request.FILES.get('file-upload'):
        uploaded_file = request.FILES['file-upload']

        error, _ = media_process(uploaded_file, request.user, None)
        if error is not None:
            context = {"status": "error", "message": str(error)}
        else:
            user_uploaded_media = Media.objects.filter(
                user=request.user,
                application_id__isnull=True
            ).order_by('-created_at')
            for media in user_uploaded_media:
                media.result_slug = media.result.lower().replace(' ', '_')
            context = {
                "status": "success",
                "message": "File uploaded successfully!",
                "uploaded_media": user_uploaded_media
            }

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

    # * Serialize the private key to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # * Generate public key
    public_key = private_key.public_key()

    # * Serialize the public key to PEM format
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return public_key_pem, private_key_pem


def validate_public_key(public_key_pem, private_key_pem):
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )

    """
    # Public key validation algorithm
    Encrypt a message using the private key to create a signature.
    Then use that signature to verify the public key. Since only 
    the correct public key can decrypt the signature. 
    """
    message = b"Message for key validation"
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"Key validation failed: {e}")
        return False


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


@login_required
def application_detail(request, id):
    application = Application.objects.get(id=id)
    return render(request, 'application-detail.html', context={'application': application})


@login_required
def update_application_status(request, application_id):
    if request.method == 'POST':
        status = request.POST.get('status')

        if application_id and status:
            application = Application.objects.get(id=application_id)
            application.status = status
            application.save()
            messages.success(request, "Application updated successfully.")
            return redirect(f'/services/applications/{application.id}')

    return redirect(f'/services/applications/{application_id}')


@login_required
def change_key(request, application_id):
    if request.method == 'GET':
        if application_id:
            application = Application.objects.get(id=application_id)
            public_key, private_key = generate_rsa_key_pair()
            application.private_key = private_key
            application.public_key = public_key
            application.save()
            messages.success(request, "Application updated successfully.")
            return redirect(f'/services/applications/{application.id}')

    return redirect(f'/services/applications/{application_id}')


def reformat_public_key_from_request(raw_public_key):
    public_key = str()
    for data in raw_public_key.split('\n'):
        if data == '-----BEGIN PUBLIC KEY-----' or data == '-----END PUBLIC KEY-----':
            continue

        data = data.replace(" ", "+")
        public_key = public_key + data + '\n'
    public_key = '-----BEGIN PUBLIC KEY-----\n' + public_key + '-----END PUBLIC KEY-----\n'
    return public_key


@csrf_exempt
def predict_service(request):
    if request.method == 'POST' and request.FILES.get('file-upload'):
        uploaded_file = request.FILES['file-upload']
        application_id = request.GET.get('application-id')
        raw_public_key_pem = request.GET.get('public-key', '')
        public_key_pem = reformat_public_key_from_request(raw_public_key_pem)

        try:
            application = Application.objects.get(id=application_id)
            user = application.user
        except Application.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Invalid application ID."},
                status=400
            )

        private_key_pem = application.private_key

        is_valid_public_key = validate_public_key(public_key_pem, private_key_pem)
        if not is_valid_public_key:
            return JsonResponse(
                {"status": "error", "message": "Unauthorized public key"},
                status=401
            )

        error, data = media_process(uploaded_file, user, application)
        if error is not None:
            return JsonResponse(
                {"status": "error", "message": "Cannot process file."},
                status=400
            )

        return JsonResponse(
            {
                "status": "success",
                "code": 200,
                "message": "File uploaded successfully!",
                "data": data,
            },
            status=200
        )
    return JsonResponse(
        {"status": "error", "message": "Invalid request or missing file."},
        status=400
    )
