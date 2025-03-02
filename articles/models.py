# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Article(models.Model):
    code_article_dem = models.CharField(primary_key=True, max_length=50)
    code_barre = models.CharField(max_length=50, null=True, blank=True)
    code_article_gen = models.CharField(max_length=50, null=True, blank=True)
    libelle = models.CharField(max_length=100, null=True, blank=True)
    code_taille = models.CharField(max_length=50, null=True, blank=True)
    lib_taille = models.CharField(max_length=100, null=True, blank=True)
    code_couleur = models.CharField(max_length=50, null=True, blank=True)
    lib_couleur = models.CharField(max_length=100, null=True, blank=True)
    code_fournisseur = models.CharField(max_length=50, null=True, blank=True)
    fam1 = models.CharField(max_length=50, null=True, blank=True)
    fam1_label = models.CharField(max_length=100, null=True, blank=True)
    fam2 = models.CharField(max_length=50, null=True, blank=True)
    fam2_label = models.CharField(max_length=100, null=True, blank=True)
    fam3 = models.CharField(max_length=50, null=True, blank=True)
    fam3_label = models.CharField(max_length=100, null=True, blank=True)
    fam4 = models.CharField(max_length=50, null=True, blank=True)
    fam4_label = models.CharField(max_length=100, null=True, blank=True)
    fam8 = models.CharField(max_length=50, null=True, blank=True)
    fam8_label = models.CharField(max_length=100, null=True, blank=True)
    date_injection = models.DateField(null=True, blank=True)
    fournisseur_principale = models.CharField(max_length=50, null=True, blank=True)
    table_libre_9 = models.CharField(max_length=50, null=True, blank=True)
    ferme = models.CharField(max_length=1, choices=[("X", "X"), ("_", "_")], default="_")

    class Meta:
        managed = True
        db_table = 'article'








