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
            name='Depot',
            fields=[
                ('code_depot', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('libelle', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'depot',
                'managed': False,
            },
        ),
    ]
