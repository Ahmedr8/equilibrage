from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from articles.models import Article
from articles.serializers import ArticleSerializer
from django.core.exceptions import ValidationError
import csv
import datetime
import os
from django.db import IntegrityError
from django.db.models import Q
from django.conf import settings


def value_verif(value):
    if value:
        if value=='NULL' or value=='':
            return None
        else:
            return value
    else:
        return None

def validate_and_format_date(date_str):
    if date_str:
        if date_str=='NULL' or date_str=='':
            return None
    else:
        return None
    try:
        # Check if the date is already in the correct format
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_str  # Return as-is if valid
    except ValueError:
        pass  # If it's not in YYYY-MM-DD, try another format

    try:
        # Attempt to parse and convert from DD/MM/YYYY to YYYY-MM-DD
        return datetime.datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None

def string_decima_format(input_string):
    # Replace comma with period
    if input_string=='NULL' or input_string=='' or input_string==None :
        return None
    row = input_string.replace(',', '.')
    try:
        # Attempt to convert to float if numeric
        return str(int(float(row)))
    except (ValueError, TypeError):
        # Return the value as-is if it's not a number
        return None

def process_csv(file_path):
    encodings = [
        'utf-8',
        'utf-8-sig',  # UTF-8 with BOM
        'utf-16',
        'latin-1',  # Also known as ISO-8859-1
        'cp1252',  # Windows-1252
    ]
    old_articles = Article.objects.all()
    unique_old_articles_keys = set(article.code_article_dem for article in old_articles)
    for encoding in encodings:
        print(encoding)
        try:
            with open(file_path, 'r', encoding=encoding) as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                articles_to_insert = []
                invalid_articles = []
                articles_to_update = []
                for row in reader:
                    while len(row) < 16:
                        row.append(None)
                    Article_instance = Article(
                        code_article_dem=row[0],
                        code_barre=string_decima_format(row[1]),
                        code_article_gen=row[2],
                        libelle=row[3],
                        code_taille=row[4],
                        lib_taille=row[5],
                        code_couleur=row[6],
                        lib_couleur=row[7],
                        code_fournisseur=row[8],
                        fam1=row[9],
                        fam1_label=row[10],
                        fam2=row[11],
                        fam2_label=row[12],
                        fam3=row[13],
                        fam3_label=row[14],
                        fam4=row[15],
                        fam4_label=row[16],
                        fam8=row[17],
                        fam8_label=row[18],
                        date_injection=validate_and_format_date(row[19]),
                        fournisseur_principale=value_verif(row[20]),
                        table_libre_9=row[21],
                        ferme=row[22] if row[22] in ["X", "_"] else "_"
                    )
                    articles_to_insert.append(Article_instance)

                unique_primary_keys = set()  # Use a set to keep track of unique primary keys
                unique_articles = []
                for article in articles_to_insert:
                    if article.code_article_dem not in unique_old_articles_keys:
                        if article.code_article_dem not in unique_primary_keys and article.code_barre:
                            unique_primary_keys.add(article.code_article_dem)
                            if article.fam1 == 'NULL' or article.fam1 == '':
                                article.fam1 = None
                            if article.fam2 == 'NULL' or article.fam2 == '':
                                article.fam2 = None
                            if article.fam3 == 'NULL' or article.fam3 == '':
                                article.fam3 = None
                            if article.fam4 == 'NULL' or article.fam4 == '':
                                article.fam4 = None
                            if article.fam8 == 'NULL' or article.fam8 == '':
                                article.fam8 = None
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
                        if article.fam8 == 'NULL' or article.fam8 == '':
                            article.fam8 = None
                        articles_to_update.append(article)
                return [unique_articles, invalid_articles, articles_to_update]
        except UnicodeDecodeError:
            continue
        except UnicodeError:
            continue


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
            now = datetime.datetime.now()
            print("before function", now.strftime("%Y-%m-%d %H:%M:%S"))
            try:
                list_res = process_csv(file_path)
            except Exception as e:
                # Handle the exception here
                print(e)
                return JsonResponse({'message': 'error proccessing csv file'}, status=status.HTTP_400_BAD_REQUEST)
            now = datetime.datetime.now()
            print("after function", now.strftime("%Y-%m-%d %H:%M:%S"))
            try:
                fields_to_update = ['code_barre', 'code_article_gen','libelle','code_taille','lib_taille','code_couleur','lib_couleur','code_fournisseur','fam1','fam2','fam3','fam4','fam8']
                Article.objects.bulk_create(list_res[0])
                Article.objects.bulk_update(list_res[2],fields_to_update)
                with open('files/'+current_date+'Articles_faile.csv', 'w') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows((article.code_article_dem,article.code_barre,article.code_article_gen,article.libelle,article.code_couleur,article.lib_couleur,article.code_taille,article.lib_taille,article.fam1,article.fam2,article.fam3,article.fam4,article.fam8) for article in list_res[1] )
                return JsonResponse({'message': 'Articles was added successfully!'}, status=status.HTTP_200_OK)
            except IntegrityError as e:
                print(e)
                return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)
    elif request.method=='DELETE':
        articles_to_delete= Article.objects.all()[(int(page_number) - 1) * page_size:(int(page_number) - 1) * page_size + page_size]
        liste_articles_to_delete_ids=set(article.code_article_dem for article in articles_to_delete)
        print(liste_articles_to_delete_ids)
        Article.objects.filter(code_article_dem__in=liste_articles_to_delete_ids).delete()
        return JsonResponse({'message': 'Articles was deleted successfully!'}, status=status.HTTP_200_OK)

def articles_filtred_list_without_pagination(request):
    if request.method == 'GET':
        code_barre = request.GET.get("code_barre")
        code_article_gen = request.GET.get("code_article_gen")
        code_fournisseur = request.GET.get("code_fournisseur")
        fournisseur_principale = request.GET.get("fournisseur_principale")
        date_injection = request.GET.get("date_injection")
        fam1 = request.GET.get("fam1")
        fam2 = request.GET.get("fam2")
        fam3 = request.GET.get("fam3")
        fam4 = request.GET.get("fam4")
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
        if fam4:
            filter_conditions &= Q(fam4=fam4)
        if fournisseur_principale:
            filter_conditions &= Q(fournisseur_principale=fournisseur_principale)
        if date_injection:
            filter_conditions &= Q(date_injection=date_injection)
        results = Article.objects.filter(filter_conditions)
        articles_serializer = ArticleSerializer(results, many=True)
        return JsonResponse(articles_serializer.data, safe=False)


def articles_gen_list(request,page_number):
    if request.method == 'GET':
        articles = Article.objects.values('code_article_gen', 'libelle', 'fam1').distinct().order_by('code_article_gen', 'libelle', 'fam1')[(int(page_number) - 1) * page_size:(int(page_number) - 1) * page_size + page_size]
        artcles_gen_list=list(articles)
        return JsonResponse(artcles_gen_list, safe=False)

def articles_gen_filtred_list(request,page_number):
    if request.method == 'GET':
        code_article_gen = request.GET.get("code_article_gen")
        code_fournisseur = request.GET.get("code_fournisseur")
        fam1 = request.GET.get("fam1")
        lib = request.GET.get("libelle")
        filter_conditions = Q()
        if code_article_gen:
            filter_conditions &= Q(code_article_gen=code_article_gen)
        if code_fournisseur:
            filter_conditions &= Q(code_fournisseur=code_fournisseur)
        if fam1:
            filter_conditions &= Q(fam1=fam1)
        if lib:
            filter_conditions &= Q(libelle=lib)
        if int(page_number) == 0:
            results=Article.objects.values('code_article_gen', 'libelle', 'fam1').filter(filter_conditions).distinct().order_by('code_article_gen', 'libelle', 'fam1')
        else:
            results = Article.objects.values('code_article_gen', 'libelle', 'fam1').filter(filter_conditions).distinct().order_by('code_article_gen', 'libelle', 'fam1')[(int(page_number) - 1) * page_size:(int(page_number) - 1) * page_size + page_size]
        results_list=list(results)
        return JsonResponse(results_list, safe=False)
def articles_filtred_list(request,page_number):
    if request.method == 'GET':
        code_barre=request.GET.get("code_barre")
        code_article_gen=request.GET.get("code_article_gen")
        code_fournisseur=request.GET.get("code_fournisseur")
        fournisseur_principale = request.GET.get("fournisseur_principale")
        date_injection = request.GET.get("date_injection")
        fam1=request.GET.get("fam1")
        fam2=request.GET.get("fam2")
        fam3=request.GET.get("fam3")
        code_couleur = request.GET.get("code_couleur")
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
        if code_couleur:
            filter_conditions &= Q(code_couleur=code_couleur)
        if fournisseur_principale:
            filter_conditions &= Q(fournisseur_principale=fournisseur_principale)
        if date_injection:
            filter_conditions &= Q(date_injection=date_injection)
        if int(page_number)==0:
            results = Article.objects.filter(filter_conditions)
        else:
            results = Article.objects.filter(filter_conditions)[(int(page_number) - 1) * page_size:(int(page_number) - 1) * page_size + page_size]
        articles_serializer = ArticleSerializer(results, many=True)
        return JsonResponse(articles_serializer.data, safe=False)

def articles_filtred_list_exist(request, page_number):
    try:
        if request.method != 'GET':
            return JsonResponse({
                'status': 'error',
                'message': 'Method not allowed'
            }, status=405)

        # Get and validate page number
        try:
            page_num = int(page_number)
            if page_num < 0:
                raise ValueError
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid page number'
            }, status=400)

        # Get filter parameters
        filters = {
            'fam1': request.GET.get("grand_famille"),
            'fam2': request.GET.get("famille"),
            'fam8': request.GET.get("besoin"),
            'code_couleur': request.GET.get("couleur"),
            'code_article_gen': request.GET.get("code_article_gen"),
            'table_libre_9': request.GET.get("solde")
        }
        print(filters)
        filter_conditions = Q()

        # Handle multi-select filters
        multi_select_fields = ['fam1', 'fam2', 'fam8', 'code_couleur']
        print(filter_conditions)
        for field in multi_select_fields:
            if filters[field]:
                values = filters[field].split(',')
                filter_conditions &= Q(**{f"{field}__in": values})
        print(filter_conditions)
        # Handle single value filters
        single_value_fields = ['code_article_gen', 'table_libre_9']
        for field in single_value_fields:
            if filters[field]:
                filter_conditions &= Q(**{field: filters[field]})
        print(filter_conditions)
        # Get base queryset
        queryset = Article.objects.filter(filter_conditions)

        # Get total count for pagination info
        total_count = queryset.count()

        # Apply pagination
        if page_num == 0:
            results = queryset
        else:
            start_idx = (page_num - 1) * page_size
            end_idx = start_idx + page_size
            results = queryset[start_idx:end_idx]

        # Serialize results
        articles_serializer = ArticleSerializer(results, many=True)

        return JsonResponse(articles_serializer.data, safe=False)

    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Validation error',
            'errors': e.messages
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def get_grand_famille_options(request):
    try:
        # Using values() and distinct() to get unique combinations
        distinct_values = Article.objects.values('fam1', 'fam1_label').distinct()

        # Format the data to match the FilterOption interface
        options = [
            {
                'value': item['fam1'],
                'label': item['fam1_label']
            }
            for item in distinct_values
            if item['fam1']  # Exclude null values
        ]

        return JsonResponse(options, safe=False)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


def get_famille_options(request):
    try:
        # Using values() and distinct() to get unique combinations
        distinct_values = Article.objects.values('fam2', 'fam2_label').distinct()

        # Format the data to match the FilterOption interface
        options = [
            {
                'value': item['fam2'],
                'label': item['fam2_label']
            }
            for item in distinct_values
            if item['fam2']  # Exclude null values
        ]

        return JsonResponse(options, safe=False)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

def get_besoin_options(request):
    try:
        # Using values() and distinct() to get unique combinations
        distinct_values = Article.objects.values('fam8', 'fam8_label').distinct()

        # Format the data to match the FilterOption interface
        options = [
            {
                'value': item['fam8'],
                'label': item['fam8_label']
            }
            for item in distinct_values
            if item['fam8']  # Exclude null values
        ]

        return JsonResponse(options, safe=False)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

def get_couleur_options(request):
    try:
        # Using values() and distinct() to get unique combinations
        distinct_values = Article.objects.values('code_couleur', 'lib_couleur').distinct()

        # Format the data to match the FilterOption interface
        options = [
            {
                'value': item['code_couleur'],
                'label': item['lib_couleur']
            }
            for item in distinct_values
            if item['code_couleur']  # Exclude null values
        ]

        return JsonResponse(options, safe=False)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
@api_view(['GET', 'PUT', 'DELETE'])
def article_detail(request, pk):
     try:
        article= Article.objects.get(code_barre=pk)
     except Article.DoesNotExist:
        return JsonResponse({'message': 'The article does not exist'}, status=status.HTTP_404_NOT_FOUND)
     if request.method == 'GET':
        article_serializer = ArticleSerializer(article)
        return JsonResponse(article_serializer.data)
     elif request.method == 'DELETE':
        article.delete()
        return JsonResponse({'message': 'Article was deleted successfully!'}, status=status.HTTP_200_OK)
     elif request.method =='PUT':
        article_data = JSONParser().parse(request)
        article_serializer = ArticleSerializer(article, data=article_data)
        if article_serializer.is_valid():
            article_serializer.save()
            return JsonResponse(article_serializer.data)
        return JsonResponse(article_serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['DELETE'])
def delete_all_records(request):
    try:
        records_to_delete = Article.objects.all()
        records_to_delete.delete()

        return JsonResponse({'message': 'All Articles deleted successfully!'}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)