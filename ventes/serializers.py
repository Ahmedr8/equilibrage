from rest_framework import serializers
from ventes.models import Vente


class VenteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vente
        fields =  '__all__'