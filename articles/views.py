from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from articles.models import Article
from articles.serializers import ArticleSerializer
import csv
import datetime
import os
from django.db import IntegrityError
from django.db.models import Q
from django.conf import settings


def process_csv(file_path):
    old_articles = Article.objects.all()
    unique_old_articles_keys = set(article.code_article_dem for article in old_articles)
    with open(file_path, 'r',encoding='utf-8-sig') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        articles_to_insert=[]
        invalid_articles=[]
        articles_to_update=[]
        for row in reader:
            Article_instance = Article(code_article_dem = row[0],code_barre = row[1],code_article_gen = row[2],libelle = row[3],code_taille = row[4],lib_taille = row[5],code_couleur = row[6],lib_couleur = row[7],code_fournisseur= row[8],fam1=row[9],fam2= row[10],fam3= row[11],fam4= row[12], fam5= row[13])
            articles_to_insert.append(Article_instance)

        unique_primary_keys = []  # Use a set to keep track of unique primary keys
        unique_articles = []
        for article in articles_to_insert:
            if article.code_article_dem not in unique_old_articles_keys:
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
            else:
                if article.fam1 == 'NULL' or article.fam1 == '':
                    article.fam1 = None
                if article.fam2 == 'NULL' or article.fam2 == '':
                    article.fam2 = None
                if article.fam3 == 'NULL' or article.fam3 == '':
                    article.fam3 = None
                if article.fam4 == 'NULL' or article.fam4 == '':
                    article.fam4 = None
                if article.fam5 == 'NULL' or article.fam5 == '':
                    article.fam5 = None
                articles_to_update.append(article)
        return [unique_articles,invalid_articles,articles_to_update]


page_size=settings.PAGINATION_PAGE_SIZE


@csrf_exempt
def articles_list(request,page_number):
    if request.method == 'GET':
            articles = Article.objects.all()[(int(page_number)-1)*page_size:(int(page_number)-1)*page_size+page_size]
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
            list_res=process_csv(file_path)
            try:
                fields_to_update = ['code_barre', 'code_article_gen','libelle','code_taille','lib_taille','code_couleur','lib_couleur','code_fournisseur','fam1','fam2','fam3','fam4','fam5']
                Article.objects.bulk_create(list_res[0])
                Article.objects.bulk_update(list_res[2],fields_to_update)
                with open('files/'+current_date+'Articles_faile.csv', 'w') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows((article.code_article_dem,article.code_barre,article.code_article_gen,article.libelle,article.code_couleur,article.lib_couleur,article.code_taille,article.lib_taille,article.fam1,article.fam2,article.fam3,article.fam4,article.fam5) for article in list_res[1] )
                return JsonResponse({'message': 'Articles was added successfully!'}, status=status.HTTP_204_NO_CONTENT)
            except IntegrityError as e:
                print(e)
                return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)
    elif request.method=='DELETE':
        articles_to_delete= Article.objects.all()[(int(page_number) - 1) * page_size:(int(page_number) - 1) * page_size + page_size]
        liste_articles_to_delete_ids=set(article.code_article_dem for article in articles_to_delete)
        print(liste_articles_to_delete_ids)
        Article.objects.filter(code_article_dem__in=liste_articles_to_delete_ids).delete()
        return JsonResponse({'message': 'Articles was deleted successfully!'}, status=status.HTTP_200_OK)



def articles_filtred_list(request,page_number):
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
        results=Article.objects.filter(filter_conditions)[(int(page_number)-1)*page_size:(int(page_number)-1)*page_size+page_size]
        print(results)
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



@api_view(['DELETE'])
def delete_all_records(request):
    try:
        records_to_delete = Article.objects.all()
        records_to_delete.delete()

        return JsonResponse({'message': 'All Articles deleted successfully!'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

