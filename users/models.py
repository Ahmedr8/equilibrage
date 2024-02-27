# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class User(models.Model):
    id_user =models.AutoField(primary_key=True)
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    tel = models.CharField(max_length=50)
    adresse = models.CharField(max_length=200)
    statut = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = 'user'

