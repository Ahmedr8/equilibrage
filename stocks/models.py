# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from articles import models as articles_models
from depots import models as depots_models
class Stock(models.Model):
    code_article_dem = models.CharField(max_length=50)
    code_etab = models.CharField(max_length=50)
    code_barre = models.CharField(max_length=50)
    stock_min = models.FloatField()
    stock_physique = models.FloatField()
    ventes = models.FloatField()
    trecu = models.IntegerField(db_column='Trecu')  # Field name made lowercase.
    t_trf_recu = models.IntegerField(db_column='T_trf_recu')  # Field name made lowercase.
    t_trf_emis = models.IntegerField(db_column='T_trf_emis')  # Field name made lowercase.
    code_depot = models.CharField(max_length=50)
    id_stock = models.AutoField(primary_key=True)

    class Meta:
        managed = True
        db_table = 'stock'
        unique_together = (('code_article_dem', 'code_depot'),)
