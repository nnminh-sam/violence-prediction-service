# Generated by Django 5.1.4 on 2024-12-21 13:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predicter', '0004_applications_created_at_media_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='application',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='media', to='predicter.applications'),
        ),
    ]