from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from depots.models import Depot
from depots.serializers import DepotSerializer
from etablissements.models import Etablissement
import csv
import datetime
import os
from django.db.models import Q
from django.db import IntegrityError
from django.conf import settings

page_size=settings.PAGINATION_PAGE_SIZE


def process_csv(file_path):
    etabs = Etablissement.objects.all()
    unique_etab_keys = set(etab.code_etab for etab in etabs)
    old_depots = Depot.objects.all()
    unique_old_depots_keys = set(depot.code_depot for depot in old_depots)
    with open(file_path, 'r',encoding='utf-8-sig') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        depots_to_insert=[]
        invalid_depots=[]
        depots_to_update=[]
        for row in reader:
            Depot_instance = Depot(code_depot = row[0],libelle = row[1],type = row[2],code_etab = row[3])
            if ((Depot_instance.code_etab in unique_etab_keys) or (Depot_instance.code_etab == 'NULL') or (Depot_instance.code_etab == '')):
                depots_to_insert.append(Depot_instance)
            else:
                invalid_depots.append(Depot_instance)
        unique_primary_keys = []  # Use a set to keep track of unique primary keys
        unique_depots= []
        for depot in depots_to_insert:
            if depot.code_depot not in unique_old_depots_keys:
                if depot.code_depot not in unique_primary_keys:
                    unique_primary_keys.append(depot.code_depot)
                    if depot.code_etab == 'NULL' or depot.code_etab == '':
                        depot.code_etab = None
                    unique_depots.append(depot)
                else:

                    invalid_depots.append(depot)
            else:
                depots_to_update.append(depot)
        return [unique_depots,invalid_depots,depots_to_update]

@csrf_exempt
def depots_list(request,page_number):
    if request.method == 'GET':
        depots = Depot.objects.all()[(int(page_number)-1)*page_size:(int(page_number)-1)*page_size+page_size]
        depots_serializer = DepotSerializer(depots, many=True)
        return JsonResponse(depots_serializer.data, safe=False)
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
            fields_to_update = ['libelle', 'type', 'code_etab']
            Depot.objects.bulk_update(list[2], fields_to_update)
            Depot.objects.bulk_create(list[0])
            with open('files/'+current_date+'Depots_faile.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows((depot.code_depot,depot.libelle,depot.type,depot.code_etab) for depot in list[1] )
            return JsonResponse({'message': 'Depots was added successfully!'}, status=status.HTTP_204_NO_CONTENT)
        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)


def depots_filtred_list(request,page_number):
    if request.method == 'GET':
        code_depot=request.GET.get("code_depot")
        print('here')
        code_etab=request.GET.get("code_etab")
        type=request.GET.get("type")
        filter_conditions = Q()
        if code_depot:
            filter_conditions &= Q(code_depot=code_depot)
        if code_etab:
            filter_conditions &= Q(code_etab=code_etab)
        if type:
            filter_conditions &= Q(type=type)
        results=Depot.objects.filter(filter_conditions)[(int(page_number)-1)*page_size:(int(page_number)-1)*page_size+page_size]
        depots_serializer = DepotSerializer(results, many=True)
        return JsonResponse(depots_serializer.data, safe=False)


@api_view(['GET', 'PUT', 'DELETE'])
def depot_detail(request, pk):
    try:
        depot= Depot.objects.get(code_depot=pk)
    except Depot.DoesNotExist:
        return JsonResponse({'message': 'depot does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        depot_serializer = DepotSerializer(depot)
        return JsonResponse(depot_serializer.data)
    elif request.method == 'DELETE':
        depot.delete()
        return JsonResponse({'message': 'depot was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
    elif request.method =='PUT':
        depot_data = JSONParser().parse(request)
        depot_serializer= DepotSerializer(depot, data=depot_data)
        if depot_serializer.is_valid():
            depot_serializer.save()
            return JsonResponse(depot_serializer.data)
        return JsonResponse(depot_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_all_records(request):
    try:
        records_to_delete = Depot.objects.all()
        records_to_delete.delete()

        return JsonResponse({'message': 'All Depots deleted successfully!'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)