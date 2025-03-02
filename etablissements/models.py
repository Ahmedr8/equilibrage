# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class Etablissement(models.Model):
    code_etab = models.CharField(primary_key=True, max_length=50)
    libelle = models.CharField(max_length=100, null=True)
    adresse1 = models.CharField(max_length=200, null=True)
    adresse2 = models.CharField(max_length=200, null=True)
    type = models.CharField(max_length=50, null=True)
    priorite = models.IntegerField(blank=True, null=True)
    secteur = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'etablissement'

