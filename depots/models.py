# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from etablissements import models as etablissementss_models
class Depot(models.Model):
    code_depot = models.CharField(primary_key=True, max_length=50)
    libelle = models.CharField(max_length=100,null=True,blank=True)
    type = models.CharField(max_length=100,null=True,blank=True)
    code_etab =models.CharField(max_length=50,null=True,blank=True)

    class Meta:
        managed = True
        db_table = 'depot'


