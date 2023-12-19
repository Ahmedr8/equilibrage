from rest_framework import serializers
from etablissements.models import Etablissement


class EtablissementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Etablissement
        fields =   '__all__'