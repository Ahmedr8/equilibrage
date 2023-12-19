


from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from articles.models import Article,Famille
from articles.serializers import ArticleSerializer,FamilleSerializer
import csv
import datetime
import os
from django.db import IntegrityError
from django.db.models import Q
def process_csv(file_path):
    familles = Famille.objects.all()
    unique_familles_keys = set(famille.code_f for famille in familles)
    with open(file_path, 'r',encoding='utf-8-sig') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        articles_to_insert=[]
        invalid_articles=[]
        for row in reader:
            Article_instance = Article(code_article_dem = row[0],code_barre = row[1],code_article_gen = row[2],libelle = row[3],code_taille = row[4],lib_taille = row[5],code_couleur = row[6],lib_couleur = row[7],code_fournisseur= row[8],fam1=row[9],fam2= row[10],fam3= row[11],fam4= row[12], fam5= row[13])
            if ((Article_instance.fam1 in unique_familles_keys) or (Article_instance.fam1 == 'NULL') or (Article_instance.fam1 == '')) and ((Article_instance.fam2 in unique_familles_keys) or (Article_instance.fam2 == 'NULL') or (Article_instance.fam2 == '')) and ((Article_instance.fam3 in unique_familles_keys) or (Article_instance.fam3 == 'NULL') or (Article_instance.fam3 == '')) and ((Article_instance.fam4 in unique_familles_keys) or (Article_instance.fam4 == 'NULL') or (Article_instance.fam4 == '')) and ((Article_instance.fam5 in unique_familles_keys) or (Article_instance.fam5 == 'NULL') or (Article_instance.fam5 == '')):
                articles_to_insert.append(Article_instance)
            else:
                invalid_articles.append(Article_instance)
        unique_primary_keys = []  # Use a set to keep track of unique primary keys
        unique_articles = []
        for article in articles_to_insert:
            if article.code_article_dem not in unique_primary_keys:
                unique_primary_keys.append(article.code_article_dem)
                if article.fam1 == 'NULL' or article.fam1== '':
                    article.fam1=None
                if article.fam2 == 'NULL' or article.fam2== '':
                    article.fam2=None
                if article.fam3 == 'NULL' or article.fam3== '':
                    article.fam3=None
                if article.fam4 == 'NULL' or article.fam4== '':
                    article.fam4=None
                if article.fam5 == 'NULL' or article.fam5== '':
                    article.fam5=None
                unique_articles.append(article)
            else:
                invalid_articles.append(article)
        print(unique_articles)
        return [unique_articles,invalid_articles]

@csrf_exempt
def articles_list(request):
    if request.method == 'GET':
            articles = Article.objects.all()
            articles_serializer = ArticleSerializer(articles, many=True)
            return JsonResponse(articles_serializer.data, safe=False)
    elif request.method == 'POST':
            file = request.FILES['file']
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            file_name = current_date + '_' + file.name
            directory = 'files'
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(os.path.join(directory, file_name), 'wb') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            file_path = 'files/'+file_name
            list=process_csv(file_path)
            try:
                count = Article.objects.all().delete()
                Article.objects.bulk_create(list[0])
                with open('files/'+current_date+'Articles_faile.csv', 'w') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows((article.code_article_dem,article.code_barre,article.code_article_gen,article.libelle,article.code_couleur,article.lib_couleur,article.code_taille,article.lib_taille,article.fam1,article.fam2,article.fam3,article.fam4,article.fam5) for article in list[1] )
                return JsonResponse({'message': 'Articles was added successfully!'}, status=status.HTTP_204_NO_CONTENT)
            except IntegrityError as e:
                print(e)
                return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)



def articles_filtred_list(request):
    if request.method == 'GET':
        code_barre=request.GET.get("code_barre")
        print('code: '+code_barre)
        code_article_gen=request.GET.get("code_article_gen")
        code_fournisseur=request.GET.get("code_fournisseur")
        fam1=request.GET.get("fam1")
        fam2=request.GET.get("fam2")
        fam3=request.GET.get("fam3")
        filter_conditions = Q()
        if code_article_gen:
            filter_conditions &= Q(code_article_gen=code_article_gen)
        if code_barre:
            filter_conditions &= Q(code_barre=code_barre)
        if code_fournisseur:
            filter_conditions &= Q(code_fournisseur=code_fournisseur)
        if fam1:
            filter_conditions &= Q(fam1=fam1)
        if fam2:
            filter_conditions &= Q(fam2=fam2)
        if fam3:
            filter_conditions &= Q(fam3=fam3)
        results=Article.objects.filter(filter_conditions)
        articles_serializer = ArticleSerializer(results, many=True)
        return JsonResponse(articles_serializer.data, safe=False)


@api_view(['GET', 'PUT', 'DELETE'])
def article_detail(request, pk):
     try:
        article= Article.objects.get(code_article_dem=pk)
     except Article.DoesNotExist:
        return JsonResponse({'message': 'The article does not exist'}, status=status.HTTP_404_NOT_FOUND)
     if request.method == 'GET':
        article_serializer = ArticleSerializer(article)
        return JsonResponse(article_serializer.data)
     elif request.method == 'DELETE':
        article.delete()
        return JsonResponse({'message': 'Article was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
     elif request.method =='PUT':
        article_data = JSONParser().parse(request)
        article_serializer = ArticleSerializer(article, data=article_data)
        if article_serializer.is_valid():
            article_serializer.save()
            return JsonResponse(article_serializer.data)
        return JsonResponse(articles_serializer.errors, status=status.HTTP_400_BAD_REQUEST)



def process_csv_f(file_path):
    with open(file_path, 'r',encoding='utf-8-sig') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        familles_to_insert=[]
        invalid_familles=[]
        for row in reader:
            Famille_instance = Famille(code_f = row[0],type = row[1],libellef = row[2],comment = None,txt_libre = None)
            familles_to_insert.append(Famille_instance)
        unique_primary_keys = []  # Use a set to keep track of unique primary keys
        unique_familles = []
        for famille in familles_to_insert:
            if famille.code_f not in unique_primary_keys:
                unique_primary_keys.append(famille.code_f)
                unique_familles.append(famille)
            else:
                invalid_familles.append(famille)
        return [unique_familles,invalid_familles]

@csrf_exempt
def familles_list(request):
    if request.method == 'GET':
        familles = Famille.objects.all()
        familles_serializer = FamilleSerializer(familles, many=True)
        return JsonResponse(familles_serializer.data, safe=False)
    elif request.method == 'POST':
        file = request.FILES['file']
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        file_name = current_date + '_' + file.name
        directory = 'files'
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(os.path.join(directory, file_name), 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        file_path = 'files/'+file_name
        list=process_csv(file_path)
        try:
            count = Famille.objects.all().delete()
            Famille.objects.bulk_create(list[0])
            with open('files/'+current_date+'Familles_faile.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows((article.code_article_dem,article.code_barre,article.code_article_gen,article.libelle,article.code_couleur,article.lib_couleur,article.code_taille,article.lib_taille,article.fam1,article.fam2,article.fam3,article.fam4,article.fam5) for article in list[1] )
            return JsonResponse({'message': 'Articles was added successfully!'}, status=status.HTTP_204_NO_CONTENT)
        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)


def familles_filtred_list(request):
    if request.method == 'GET':
        code_f=request.GET.get("code_f")
        type=request.GET.get("type")
        libellef=request.GET.get("libellef")
        filter_conditions = Q()
        if code_f:
            filter_conditions &= Q(code_f=code_f)
        if type:
            filter_conditions &= Q(type=type)
        if libellef:
            filter_conditions &= Q(libellef=libellef)
        results=Famille.objects.filter(filter_conditions)
        familles_serializer = FamilleSerializer(results, many=True)
        return JsonResponse(familles_serializer.data, safe=False)


@api_view(['GET', 'PUT', 'DELETE'])
def famille_detail(request, pk):
    try:
        famille= Famille.objects.get(code_f=pk)
    except Famille.DoesNotExist:
        return JsonResponse({'message': 'Famille does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        famille_serializer = FamilleSerializer(famille)
        return JsonResponse(famille_serializer.data)
    elif request.method == 'DELETE':
        famille.delete()
        return JsonResponse({'message': 'Famille was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
    elif request.method =='PUT':
        famille_data = JSONParser().parse(request)
        famille_serializer = FamilleSerializer(famille, data=famille_data)
        if famille_serializer.is_valid():
            famille_serializer.save()
            return JsonResponse(famille_serializer.data)
        return JsonResponse(famille_serializer.errors, status=status.HTTP_400_BAD_REQUEST)