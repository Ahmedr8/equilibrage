from rest_framework import serializers
from articles.models import Article
from articles.models import Famille

class ArticleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Article
        fields =  '__all__'

class FamilleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Famille
        fields = '__all__'