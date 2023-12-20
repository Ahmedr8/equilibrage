# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2023-07-17 13:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id_user', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('nom', models.CharField(max_length=50)),
                ('prenom', models.CharField(max_length=50)),
                ('tel', models.CharField(max_length=50)),
                ('adresse', models.CharField(max_length=200)),
                ('statut', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'user',
                'managed': False,
            },
        ),
    ]