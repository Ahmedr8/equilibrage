# Generated by Django 4.2.3 on 2024-12-26 22:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trf_sessions', '0003_proposition_stock_emet_sera_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposition',
            name='stock_emet_sera_couleur',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='proposition',
            name='stock_recep_sera_couleur',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
