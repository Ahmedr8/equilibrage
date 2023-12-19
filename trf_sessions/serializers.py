from rest_framework import serializers
from trf_sessions.models import EnteteSession,DetailleSession,Proposition


class SessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = EnteteSession
        fields = '__all__'

class DetailleSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DetailleSession
        fields =  '__all__'

class PropositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Proposition
        fields =  '__all__'
