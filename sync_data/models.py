from django.db import models

class ParamSynchro(models.Model):
    workspace = models.CharField(primary_key=True,max_length=255)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    environment = models.CharField(max_length=50)
    container_name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'ParamSynchro'

class SyncLog(models.Model):
    file_name = models.CharField(max_length=255)
    sync_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50)
    error_message = models.TextField(null=True, blank=True)

class SyncStatus:
    def __init__(self):
        self.status = False
        self.log = None