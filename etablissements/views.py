from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from etablissements.models import Etablissement
from etablissements.serializers import EtablissementSerializer
import csv
import datetime
import os
from django.db.models import Q
from django.db import IntegrityError
def process_csv(file_path):
    old_etablissements = Etablissement.objects.all()
    unique_old_etablissements_keys = set(etab.code_etab for etab in old_etablissements)
    with open(file_path, 'r',encoding='utf-8-sig') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        etablissements_to_insert=[]
        invalid_etablissements=[]
        etablissements_to_update=[]
        for row in reader:
            if "siege" in row[4]:
                prio=1000
            else:
                prio=0
            Etablissement_instance = Etablissement(code_etab = row[0],libelle = row[1],adresse1 = row[2],adresse2 = row[3],type = row[4],priorite = prio)
            etablissements_to_insert.append(Etablissement_instance)
        unique_primary_keys = []  # Use a set to keep track of unique primary keys
        unique_etablissements= []
        for etab in etablissements_to_insert:
            if etab.code_etab not in unique_old_etablissements_keys:
                if etab.code_etab not in unique_primary_keys:
                    unique_primary_keys.append(etab.code_etab)
                    unique_etablissements.append(etab)
                else:
                    invalid_etablissements.append(etab)
            else:
                etablissements_to_update.append(etab)
        return [unique_etablissements,invalid_etablissements,etablissements_to_update]

@csrf_exempt
def etablissements_list(request):
    if request.method == 'GET':
        etablissements = Etablissement.objects.all()
        etablissements_serializer = EtablissementSerializer(etablissements, many=True)
        return JsonResponse(etablissements_serializer.data, safe=False)
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
            print(list[0])
            print(list[1])
            print(list[2])
            fields_to_update = ['libelle', 'adresse1', 'adresse2','type','priorite']
            Etablissement.objects.bulk_update(list[2], fields_to_update)
            Etablissement.objects.bulk_create(list[0])
            with open('files/'+current_date+'Etablissement_faile.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows((etab.code_etab,etab.libelle,etab.adresse1,etab.adresse2,etab.type) for etab in list[1] )
            return JsonResponse({'message': 'Etablissements was added successfully!'}, status=status.HTTP_204_NO_CONTENT)
        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)


def etablissements_filtred_list(request):
    if request.method == 'GET':
        code_etab=request.GET.get("code_etab")
        adresse1=request.GET.get("adresse1")
        type=request.GET.get("type")
        filter_conditions = Q()
        if code_etab:
            filter_conditions &= Q(code_etab=code_etab)
        if adresse1:
            filter_conditions &= Q(adresse1=adresse1)
        if type:
            filter_conditions &= Q(type=type)
        results=Etablissement.objects.filter(filter_conditions)
        etablissements_serializer = EtablissementSerializer(results, many=True)
        return JsonResponse(etablissements_serializer.data, safe=False)


@api_view(['GET', 'PUT', 'DELETE'])
def etablissement_detail(request, pk):
    try:
        etab= Etablissement.objects.get(code_etab=pk)
    except Etablissement.DoesNotExist:
        return JsonResponse({'message': 'The etablissment does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        etablissement_serializer = EtablissementSerializer(etab)
        return JsonResponse(etablissement_serializer.data)
    elif request.method == 'DELETE':
        etab.delete()
        return JsonResponse({'message': 'Etablissment was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
    elif request.method =='PUT':
        etab_data = JSONParser().parse(request)
        prio = etab_data.get('priorite')
        etab.priorite=prio
        print(prio)
        print(etab.priorite)
        if etab.priorite>=0:
            etab.save()
            return JsonResponse({'message': 'Property updated successfully.'}, status=200)
        return JsonResponse({'message': 'error.'}, status=500)
