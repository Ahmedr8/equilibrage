


from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from stocks.models import Stock
from stocks.serializers import StockSerializer
from articles.models import Article,Famille
from depots.models import Depot
from etablissements.models import Etablissement
import csv
import datetime
import os
from django.db.models import Q
from django.db import IntegrityError
def process_csv(file_path):
    articles = Article.objects.all()
    depots = Depot.objects.all()
    etabs=Etablissement.objects.all()
    unique_articles_keys = set(article.code_article_dem for article in articles)
    unique_depots_keys = set(depot.code_depot for depot in depots)
    unique_etabs_keys = set(etab.code_etab for etab in etabs)
    with open(file_path, 'r',encoding='utf-8-sig') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        stocks_to_insert=[]
        invalid_stocks=[]
        for row in reader:
            Stock_instance = Stock(code_article_dem = row[0],code_barre = row[1],stock_physique = row[2],stock_min = row[3],ventes = row[4],trecu = row[5],t_trf_recu = row[6],t_trf_emis = row[7],code_depot=row[8],code_etab=row[9])
            if (Stock_instance.code_article_dem in unique_articles_keys)  and (Stock_instance.code_depot in unique_depots_keys) and ((Stock_instance.code_etab in unique_etabs_keys) or (Stock_instance.code_etab == 'NULL') or (Stock_instance.code_etab == '')) and (Stock_instance.stock_min !='NULL') and (Stock_instance.stock_physique !='NULL') :
                stocks_to_insert.append(Stock_instance)
            else:
                invalid_stocks.append(Stock_instance)
        unique_primary_keys = []  # Use a set to keep track of unique primary keys
        unique_stocks = []
        for stock in stocks_to_insert:
            if (stock.code_article_dem+stock.code_depot not in unique_primary_keys):
                unique_primary_keys.append(stock.code_article_dem+stock.code_depot)
                if stock.code_etab == 'NULL' or stock.code_etab== '':
                    depot= Depot.objects.get(code_depot=stock.code_depot)
                    stock.code_etab=depot.code_etab
                if stock.t_trf_emis =='NULL' or stock.t_trf_emis == '':
                    stock.t_trf_emis=None
                if stock.trecu =='NULL' or stock.trecu == '':
                    stock.trecu=None
                if stock.t_trf_recu =='NULL' or stock.t_trf_recu == '':
                    stock.t_trf_recu=None
                if stock.ventes =='NULL' or stock.ventes == '':
                    stock.ventes=None
                unique_stocks.append(stock)
            else:
                invalid_stocks.append(stock)
        return [unique_stocks,invalid_stocks]

@csrf_exempt
def stocks_list(request):
    if request.method == 'GET':
        stocks = Stock.objects.all()
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
        list=process_csv(file_path)
        try:
            count = Stock.objects.all().delete()
            Stock.objects.bulk_create(list[0])
            with open('files/'+current_date+'Stocks_faile.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows((stock.code_article_dem,stock.code_barre,stock.stock_physique,stock.stock_min,stock.ventes,stock.trecu,stock.t_trf_recu,stock.t_trf_emis,stock.code_depot,stock.code_etab) for stock in list[1] )
            return JsonResponse({'message': 'Stocks was added successfully!'}, status=status.HTTP_204_NO_CONTENT)
        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)

def stocks_filtred_list(request):
    if request.method == 'GET':
        code_barre=request.GET.get("code_barre")
        code_etab=request.GET.get("code_etab")
        code_depot=request.GET.get("code_depot")
        filter_conditions = Q()
        if code_etab:
            filter_conditions &= Q(code_etab=code_etab)
        if code_barre:
            filter_conditions &= Q(code_barre=code_barre)
        if code_depot:
            filter_conditions &= Q(code_depot=code_depot)
        results=Stock.objects.filter(filter_conditions)
        stocks_serializer = StockSerializer(results, many=True)
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
        return JsonResponse({'message': 'stock was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
    elif request.method =='PUT':
        stock_data = JSONParser().parse(request)
        stock_serializer = StockSerializer(stock, data=stock_data)
        if stock_serializer.is_valid():
            stock_serializer.save()
            return JsonResponse(stock_serializer.data)
        return JsonResponse(stock_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
