# Generated by Django 4.2.3 on 2024-04-08 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0003_alter_article_date_injection'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='fournisseur_principale',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]