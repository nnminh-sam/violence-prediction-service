from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User


class Applications(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    public_key = models.CharField(max_length=255, unique=True)
    private_key = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    created_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'applications'


class Media(models.Model):
    RESULT_CHOICES = [
        ('violence', 'Violence'),
        ('non violence', 'Non Violence'),
        ('undefined', 'Undefined'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    original_name = models.CharField(max_length=255)
    local_path = models.CharField(max_length=255)
    size_bytes = models.IntegerField()
    duration = models.FloatField(null=True, blank=True)
    resolution = models.CharField(max_length=50, null=True, blank=True)
    result = models.CharField(max_length=12, choices=RESULT_CHOICES, default='undefined')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="media")
    created_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.original_name} ({self.name}) - {self.size_bytes} Bytes"

    class Meta:
        db_table = 'media'
