# Generated by Django 4.2.3 on 2024-03-03 19:34

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='date_injection',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]