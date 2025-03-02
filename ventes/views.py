from django.http import JsonResponse

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
from django.db import transaction
from django.db.models import Q


def process_csv(file_path):
    etabs = Etablissement.objects.all()
    unique_etabs_keys = set(etab.code_etab for etab in etabs)
    articles = Article.objects.all()
    unique_articles_keys = set(article.code_barre for article in articles)
    old_ventes = Vente.objects.all()
    unique_old_ventes_keys = set(vente.num_ticket + vente.num_ligne + vente.code_etab + vente.code_barre for vente in old_ventes)
    encodings = [
        'utf-8', 'utf-8-sig', 'utf-16', 'latin-1', 'cp1252'
    ]

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                ventes_to_insert = []
                ventes_to_update = []
                invalid_ventes = []
                unique_ventes = set()
                for row in reader:
                    # Ensure minimum row length
                    while len(row) < 7:
                        row.append(None)

                    date_vente = datetime.datetime.strptime(row[0], "%d/%m/%Y")

                    try:
                        # Create the Vente instance with ticket and ligne
                        vente_instance = Vente(
                            date_ventes=date_vente,
                            code_article=row[1],
                            code_barre=row[2],
                            qte=row[3],
                            code_etab=row[4],
                            num_ticket=row[5],
                            num_ligne=row[6]
                        )

                        # Validate the instance
                        vente_instance.full_clean()

                        # Check for existing record to update
                        if_existing_vente = (vente_instance.num_ticket+vente_instance.num_ligne+vente_instance.code_etab+vente_instance.code_barre) in unique_old_ventes_keys
                        if if_existing_vente:
                            ventes_to_update.append(vente_instance)

                        # Check etablissement and article codes
                        if ((vente_instance.code_etab in unique_etabs_keys) and (
                                vente_instance.code_barre in unique_articles_keys)):

                            if not if_existing_vente:
                                if ((vente_instance.num_ticket + vente_instance.num_ligne + vente_instance.code_etab + vente_instance.code_barre) in unique_ventes):
                                    vente_instance.code_article = "line eplicated with the same num ticket, num ligne, code etab and code barre"
                                    invalid_ventes.append(vente_instance)
                                else:
                                    unique_ventes.add(vente_instance.num_ticket + vente_instance.num_ligne + vente_instance.code_etab + vente_instance.code_barre)
                                    ventes_to_insert.append(vente_instance)
                        else:
                            vente_instance.code_article = "integrity error on code barre or code etab"
                            invalid_ventes.append(vente_instance)

                    except ValidationError as e:
                        fail_instance = Vente(
                            date_ventes=date_vente,
                            code_article=str(e.message_dict),
                            code_barre=row[2],
                            qte=row[3],
                            code_etab=row[4],
                            num_ticket=row[5],
                            num_ligne=row[6]
                        )
                        invalid_ventes.append(fail_instance)
                        print("Validation error occurred:", e.message_dict)

                return [ventes_to_insert, ventes_to_update, invalid_ventes]

        except UnicodeDecodeError:
            continue
        except UnicodeError:
            continue

def batch_process_updates(vente_updates, batch_size=1000):
    """
    Process stock updates in batches to avoid parameter limit issues.

    Args:
        stock_updates: List of stock update objects
        batch_size: Number of records to process in each batch
    """
    # Process in batches
    for i in range(0, len(vente_updates), batch_size):
        batch = vente_updates[i:i + batch_size]

        # Build query for current batch
        query = Q()
        for vente_update in batch:
            query |= Q(
                code_barre=vente_update.code_barre,
                code_etab=vente_update.code_etab,
                num_ticket=vente_update.num_ticket,
                num_ligne=vente_update.num_ligne,
            )

        # Delete and create in a transaction to ensure data consistency
        with transaction.atomic():
            # Delete matching records for current batch
            Vente.objects.filter(query).delete()

            # Create new records for current batch
            Vente.objects.bulk_create(batch)

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

        file_path = 'files/' + file_name

        try:
            result_list = process_csv(file_path)
        except Exception as e:
            print(e)
            return JsonResponse({'message': 'error processing csv file'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Bulk create new ventes
            Vente.objects.bulk_create(result_list[0])

            batch_process_updates(result_list[1], batch_size=500)

            # Write invalid ventes to a CSV file
            with open('files/' + current_date + 'Ventes_failed.csv', 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(
                    (vente.date_ventes, vente.code_barre, vente.code_article, vente.qte, vente.code_etab)
                    for vente in result_list[2]
                )

            return JsonResponse({
                'message': 'Ventes added and updated successfully!',
                'inserted': len(result_list[0]),
                'updated': len(result_list[1]),
                'invalid': len(result_list[2])
            }, status=status.HTTP_200_OK)

        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)