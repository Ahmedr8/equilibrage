


from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from stocks.models import Stock
from stocks.serializers import StockSerializer
from articles.models import Article
from depots.models import Depot
from etablissements.models import Etablissement
import csv
import datetime
import os
from django.db.models import Q
from django.db import IntegrityError
from django.conf import settings
from django.db import connection
from django.db import transaction

page_size=settings.PAGINATION_PAGE_SIZE

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
    articles = Article.objects.all()
    depots = Depot.objects.all()
    etabs=Etablissement.objects.all()
    old_stocks = Stock.objects.all()
    unique_old_stocks_keys = set(stock.code_article_dem+stock.code_depot for stock in old_stocks)
    unique_articles_keys = set(article.code_article_dem for article in articles)
    unique_depots_keys = set(depot.code_depot for depot in depots)
    unique_etabs_keys = set(etab.code_etab for etab in etabs)
    encodings = [
        'utf-8',
        'utf-8-sig',  # UTF-8 with BOM
        'utf-16',
        'latin-1',  # Also known as ISO-8859-1
        'cp1252',  # Windows-1252
    ]

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                stocks_to_insert = []
                invalid_stocks = []
                stocks_to_update = []
                for row in reader:
                    while len(row) < 10:
                        row.append(None)
                    Stock_instance = Stock(code_article_dem=row[0], code_barre=string_decima_format(row[1]),
                                           stock_physique=row[2], stock_min=row[3], ventes=row[4], trecu=row[5],
                                           t_trf_recu=row[7], t_trf_emis=row[6], code_depot=row[8], code_etab=row[9])
                    if (Stock_instance.code_article_dem in unique_articles_keys) and (
                            Stock_instance.code_depot in unique_depots_keys) and (
                            (Stock_instance.code_etab in unique_etabs_keys) or (Stock_instance.code_etab == 'NULL') or (
                            Stock_instance.code_etab == '')) and (Stock_instance.stock_min != 'NULL') and (
                            Stock_instance.stock_physique != 'NULL'):
                        stocks_to_insert.append(Stock_instance)
                    else:
                        Stock_instance.code_etab = " error : code depot ou Code à barres non valide"
                        invalid_stocks.append(Stock_instance)
                unique_primary_keys = set()  # Use a set to keep track of unique primary keys
                unique_stocks = []
                for stock in stocks_to_insert:
                    if (stock.code_article_dem + stock.code_depot not in unique_old_stocks_keys):
                        if (stock.code_article_dem + stock.code_depot not in unique_primary_keys):
                            unique_primary_keys.add(stock.code_article_dem + stock.code_depot)
                            if stock.code_etab == 'NULL' or stock.code_etab == '':
                                depot = Depot.objects.get(code_depot=stock.code_depot)
                                stock.code_etab = depot.code_etab
                            if stock.t_trf_emis == 'NULL' or stock.t_trf_emis == '':
                                stock.t_trf_emis = 0
                            if stock.trecu == 'NULL' or stock.trecu == '':
                                stock.trecu = 0
                            if stock.t_trf_recu == 'NULL' or stock.t_trf_recu == '':
                                stock.t_trf_recu = 0
                            if stock.ventes == 'NULL' or stock.ventes == '':
                                stock.ventes = 0
                            unique_stocks.append(stock)
                        else:
                            stock.code_etab="integrity  error : code depot avec Code à barres dupliqué"
                            invalid_stocks.append(stock)
                    else:
                        if stock.code_etab == 'NULL' or stock.code_etab == '':
                            depot = Depot.objects.get(code_depot=stock.code_depot)
                            stock.code_etab = depot.code_etab
                        if stock.t_trf_emis == 'NULL' or stock.t_trf_emis == '':
                            stock.t_trf_emis = 0
                        if stock.trecu == 'NULL' or stock.trecu == '':
                            stock.trecu = 0
                        if stock.t_trf_recu == 'NULL' or stock.t_trf_recu == '':
                            stock.t_trf_recu = 0
                        if stock.ventes == 'NULL' or stock.ventes == '':
                            stock.ventes = 0
                        stocks_to_update.append(stock)
                return [unique_stocks, invalid_stocks, stocks_to_update]
        except UnicodeDecodeError:
            continue
        except UnicodeError:
            continue


def batch_process_updates(stock_updates, batch_size=5000):
    """
    Process stock updates in batches to avoid parameter limit issues.

    Args:
        stock_updates: List of stock update objects
        batch_size: Number of records to process in each batch
    """
    # Process in batches
    for i in range(0, len(stock_updates), batch_size):
        batch = stock_updates[i:i + batch_size]

        # Build query for current batch
        query = Q()
        for stock_update in batch:
            query |= Q(
                code_article_dem=stock_update.code_article_dem,
                code_depot=stock_update.code_depot
            )

        # Delete and create in a transaction to ensure data consistency
        with transaction.atomic():
            # Delete matching records for current batch
            Stock.objects.filter(query).delete()

            # Create new records for current batch
            Stock.objects.bulk_create(batch)
def bulk_create_in_batches(data_list, batch_size=50000):
    for i in range(0, len(data_list), batch_size):
        with transaction.atomic():
            Stock.objects.bulk_create(data_list[i:i+batch_size])
@csrf_exempt
def stocks_list(request,page_number):
    if request.method == 'GET':
        stocks = Stock.objects.all()[(int(page_number)-1)*page_size:(int(page_number)-1)*page_size+page_size]
        stocks_serializer = StockSerializer(stocks, many=True)
        return JsonResponse(stocks_serializer.data, safe=False)
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
        try:
            list=process_csv(file_path)
        except Exception as e:
            print(e)
            # Handle the exception here
            return JsonResponse({'message': 'error proccessing csv file'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            batch_process_updates(list[2], batch_size=1000)
            bulk_create_in_batches(list[0])
            with open('files/'+current_date+'Stocks_faile.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows((stock.code_article_dem,stock.code_barre,stock.stock_physique,stock.stock_min,stock.ventes,stock.trecu,stock.t_trf_recu,stock.t_trf_emis,stock.code_depot,stock.code_etab) for stock in list[1] )
            return JsonResponse({'message': 'Stocks was added successfully!'}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)

def stocks_filtred_list(request,page_number):
    if request.method == 'GET':
        code_barre=request.GET.get("code_barre")
        code_etab=request.GET.get("code_etab")
        code_depot=request.GET.get("code_depot")
        fam1=request.GET.get("fam1")
        fam2=request.GET.get("fam2")
        fam3=request.GET.get("fam3")
        filter_conditions = Q()
        if fam1 or fam2 or fam3:
            with connection.cursor() as cursor:
                cursor.execute("SELECT  s.* from stock s , article a where a.code_article_dem=s.code_article_dem and (s.code_etab=%s or s.code_barre=%s or s.code_depot=%s or a.fam1=%s or a.fam2=%s or a.fam3=%s ) ",[code_etab,code_barre,code_depot,fam1,fam2,fam3])
                results_with_fam = cursor.fetchall()
                results=[
                    Stock(code_article_dem=row[0], code_barre=row[2], stock_physique=row[4], stock_min=row[3],ventes=row[5], trecu=row[6], t_trf_recu=row[7], t_trf_emis=row[8], code_depot=row[9],code_etab=row[1])
                    for row in results_with_fam
                ]
        else:
            if code_etab:
                filter_conditions &= Q(code_etab=code_etab)
            if code_barre:
                filter_conditions &= Q(code_barre=code_barre)
            if code_depot:
                filter_conditions &= Q(code_depot=code_depot)
            results = Stock.objects.filter(filter_conditions)
        stocks_serializer = StockSerializer(results[(int(page_number) - 1) * page_size:(int(page_number) - 1) * page_size + page_size], many=True)
        return JsonResponse(stocks_serializer.data, safe=False)



@api_view(['GET', 'PUT', 'DELETE'])
def stock_detail(request, pk):
    try:
        stock= Stock.objects.get(id_stock=pk)
    except Stock.DoesNotExist:
        return JsonResponse({'message': 'stock does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        stock_serializer = StockSerializer(stock)
        return JsonResponse(stock_serializer.data)
    elif request.method == 'DELETE':
        stock.delete()
        return JsonResponse({'message': 'stock was deleted successfully!'}, status=status.HTTP_200_OK)
    elif request.method =='PUT':
        stock_data = JSONParser().parse(request)
        stock_serializer = StockSerializer(stock, data=stock_data)
        if stock_serializer.is_valid():
            stock_serializer.save()
            return JsonResponse(stock_serializer.data)
        return JsonResponse(stock_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_all_records(request):
    try:
        records_to_delete = Article.objects.all()
        records_to_delete.delete()

        return JsonResponse({'message': 'All Stock deleted successfully!'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)