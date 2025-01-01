# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from etablissements import models as etablissementss_models
from django.db import models
from articles import models as articles_models
from users import models as users_models

class EnteteSession(models.Model):
    code_session = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=100)
    date = models.DateField()
    id_user = models.IntegerField(db_column='id_user')
    critere = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = 'entete_session'



class DetailleSession(models.Model):
    id_detaille = models.AutoField(primary_key=True)
    code_session = models.IntegerField(db_column='code_session')
    code_article_dem = models.CharField(max_length=50,null=True)
    code_etab = models.CharField(max_length=50,null=True)
    stock_physique = models.FloatField()
    stock_min = models.FloatField()

    class Meta:
        managed = True
        db_table = 'detaille_session'


class Proposition(models.Model):
    code_prop = models.AutoField(primary_key=True)
    code_detaille_emet = models.IntegerField(db_column='code_detaille_emet')
    code_detaille_recep = models.IntegerField(db_column='code_detaille_recep')
    qte_trf = models.FloatField()
    statut = models.CharField(max_length=100)
    etat = models.CharField(max_length=100)
    stock_recep_sera = models.FloatField(null=True, blank=True)
    stock_emet_sera = models.FloatField(null=True, blank=True)
    stock_recep_sera_couleur = models.FloatField(null=True, blank=True)
    stock_emet_sera_couleur = models.FloatField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'proposition'
