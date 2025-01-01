from rest_framework import serializers
from sync_data.models import ParamSynchro,SyncLog


class ParamSynchroSerializer(serializers.ModelSerializer):
    destination_path = serializers.CharField(write_only=True,required=False)

    class Meta:
        model = ParamSynchro
        fields =  '__all__'
class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields =   '__all__'