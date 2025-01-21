
from django.http import JsonResponse
from django.shortcuts import render

from articles.models import Article
from django.views.decorators.csrf import csrf_exempt
from etablissements.models import Etablissement
from ventes.models import Vente
from django.core.exceptions import ValidationError
import csv
import datetime
import os
from ventes.serializers import VenteSerializer
from rest_framework import status
from django.db import IntegrityError
def process_csv(file_path):
    etabs = Etablissement.objects.all()
    unique_etabs_keys = set(etab.code_etab for etab in etabs)
    articles = Article.objects.all()
    unique_articles_keys = set(article.code_barre for article in articles)
    encodings = [
        'utf-8',
        'utf-8-sig',  # UTF-8 with BOM
        'utf-16',
        'latin-1',  # Also known as ISO-8859-1
        'cp1252',  # Windows-1252
    ]

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding ) as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                ventes_to_insert = []
                invalid_ventes = []
                for row in reader:
                    while len(row) < 5:
                        row.append(None)
                    date_vente = datetime.datetime.strptime(row[0], "%d/%m/%Y")
                    try:
                        # Create the Vente instance
                        Vente_instance = Vente(
                            date_ventes=date_vente,
                            code_article=row[1],
                            code_barre=row[2],
                            qte=row[3],
                            code_etab=row[4]
                        )
                        # Validate the instance

                        Vente_instance.full_clean()
                        if ((Vente_instance.code_etab in unique_etabs_keys) and (
                                Vente_instance.code_barre in unique_articles_keys)):
                            ventes_to_insert.append(Vente_instance)
                        else:
                            Vente_instance.code_article = "integritiy error on code barre or code etab"
                            invalid_ventes.append(Vente_instance)
                    except ValidationError as e:
                        fail_instance = Vente(
                            date_ventes=date_vente,
                            code_article=e.message_dict,
                            code_barre=row[2],
                            qte=row[3],
                            code_etab=row[4]
                        )
                        invalid_ventes.append(fail_instance)
                        print("Validation error occurred:", e.message_dict)
                return [ventes_to_insert, invalid_ventes]
        except UnicodeDecodeError:
            continue
@csrf_exempt
def ventes_list(request):
    if request.method == 'GET':
        ventes = Vente.objects.all()
        ventes_serializer = VenteSerializer(ventes, many=True)
        return JsonResponse(ventes_serializer.data, safe=False)
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
            Vente.objects.bulk_create(list[0])
            with open('files/'+current_date+'Ventes_faile.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows((vente.date_ventes,vente.code_barre,vente.code_article,vente.qte,vente.code_etab) for vente in list[1] )
            return JsonResponse({'message': 'Ventes was added successfully!'}, status=status.HTTP_200_OK)
        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)