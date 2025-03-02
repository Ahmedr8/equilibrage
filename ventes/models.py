from django.db import models

class Vente(models.Model):
    date_ventes = models.DateField()
    code_article = models.CharField(max_length=100)  # Code for the article
    code_barre = models.CharField(max_length=50)  # Barcode for the product
    qte = models.IntegerField()  # Quantity sold
    code_etab = models.CharField(max_length=20)  # Establishment code
    num_ticket=models.CharField(max_length=20)
    num_ligne = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = 'ventes'