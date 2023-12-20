from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from trf_sessions.models import EnteteSession,DetailleSession,Proposition
from articles.models import Article
from etablissements.models import Etablissement
from stocks.models import Stock
from trf_sessions.serializers import SessionSerializer,DetailleSessionSerializer,PropositionSerializer
from django.db import IntegrityError
from django.db import connection
from django.db.models import Q
import json
from django.db import connection
from django.conf import settings

page_size=settings.PAGINATION_PAGE_SIZE


@csrf_exempt
def sessions_list(request,page_number):
    if request.method == 'GET':
        sessions = EnteteSession.objects.all()[(int(page_number)-1)*page_size:(int(page_number)-1)*page_size+page_size+1]
        sessions_serializer = SessionSerializer(sessions, many=True)
        return JsonResponse(sessions_serializer.data, safe=False)
    elif request.method == 'POST':
        session_data = JSONParser().parse(request)
        session_serializer =SessionSerializer(data=session_data)
        if session_serializer.is_valid():
            session_serializer.save()
            return JsonResponse(session_serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(session_serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET', 'PUT','DELETE'])
def session_detail(request, pk):
    try:
        session= EnteteSession.objects.get(code_session=pk)
    except EnteteSession.DoesNotExist:
        return JsonResponse({'message': 'session does not exist'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        try:
            dets = DetailleSession.objects.filter(code_session=pk).values()
            dets_serializer = DetailleSessionSerializer(dets, many=True)
            return JsonResponse(dets_serializer.data, safe=False)
        except EnteteSession.DoesNotExist:
            return JsonResponse({'message': 'session does not exist'}, status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'DELETE':
        session.delete()
        return JsonResponse({'message': 'session was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)
    elif request.method =='PUT':
        session_data = JSONParser().parse(request)
        session_serializer = SessionSerializer(session, data=session_data)
        if session_serializer.is_valid():
            session_serializer.save()
            return JsonResponse(session_serializer.data)
        return JsonResponse(session_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def custom_sort_key(element):
    print(element)
    if "siege" in element[4]:
        print('siege')
        return 0
    else:
        return 1
@api_view(['POST'])
def post_session_detail(request,pk):
    if request.method == 'POST':
        try:
            json_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data.'}, status=400)
        articles = json_data.get('articles', [])
        etabs = json_data.get('etabs', [])
        print("articles:", articles)
        print("etabs:", etabs)
        d_session=[]
        d_sessionf=[]
        id_s=pk
        sql_query ="SELECT s.id_stock,s.code_article_dem,s.code_etab,e.priorite,e.type,SUM(s.stock_physique) as stock_physique,s.stock_min FROM stock s,depot d,etablissement e where s.code_depot=d.code_depot and d.code_etab=e.code_etab GROUP by s.code_article_dem,s.code_etab"
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
        for details in results:
            print(details)
            details_instance=DetailleSession(code_session=id_s,code_article_dem=details[1],code_etab=details[2],stock_physique=details[5],stock_min=details[6])
            if (details_instance.code_etab in etabs) and (details_instance.code_article_dem in articles):
                d_session.append(details_instance)
                d_sessionf.append(details)
            elif (details_instance.code_etab in etabs):
                details_instance.code_article_dem=None
                d_session.append(details_instance)
            elif  (details_instance.code_article_dem in articles):
                details_instance.code_etab=None
                d_session.append(details_instance)
        try:
            print("detaill finale :",d_sessionf)
            DetailleSession.objects.bulk_create(d_session)
            propositions=[]
            for code_article in articles:
                offre=[]
                offre1=[]
                demande=[]
                for details in d_sessionf:
                    if (details[1] == code_article):
                        if details[5] > details[6] :
                            new_details = details + (details[5]-details[6],)
                            # setattr(details, 'val',details.stock_physique-details.stock_min )
                            offre1.append(new_details)
                        elif details[5] < details[6]:
                            new_details = details + (details[6]-details[5],)
                            #setattr(details, 'val', details.stock_min-details.stock_physique)
                            demande.append(new_details)
                offre1.sort(key= lambda x:x[7], reverse=True)
                demande.sort(key= lambda  x:(x[3],x[7]), reverse=True)
                print('tri')
                # offre = sorted(offre1, key=custom_sort_key)
                list_list=[list(t) for t in offre1]
                list_list_dem=[list(d) for d in demande]
                offre=list_list
                demande=list_list_dem
                print(offre)
                print(demande)
                i=0
                while offre and demande :
                    id_emet=DetailleSession.objects.get(code_article_dem=offre[i][1],code_etab=offre[i][2],code_session=id_s)
                    id_recep=DetailleSession.objects.get(code_article_dem=demande[i][1],code_etab=demande[i][2],code_session=id_s)
                    if offre[i][7] > demande[i][7]:
                        qte=demande[i][7]
                        prop=Proposition(code_detaille_emet=id_emet.id_detaille,code_detaille_recep=id_recep.id_detaille,qte_trf=qte,statut="en cours",etat="non modifier")
                        offre[i][7]=offre[i][7]-demande[i][7]
                        del demande[i]
                    elif offre[i][7] < demande[i][7]:
                        qte=offre[i][7]
                        prop=Proposition(code_detaille_emet=id_emet.id_detaille,code_detaille_recep=id_recep.id_detaille,qte_trf=qte,statut="en cours",etat="non modifier")
                        demande[i][7]=demande[i][7]-offre[i][7]
                        del offre[i]
                    else:
                        qte=offre[i][7]
                        prop=Proposition(code_detaille_emet=id_emet.id_detaille,code_detaille_recep=id_recep.id_detaille,qte_trf=qte,statut="en cours",etat="non modifier")
                        del offre[i]
                        del demande[i]
                    propositions.append(prop)
            print(propositions)
            try:
                Proposition.objects.bulk_create(propositions)
            except IntegrityError as e:
                print(e)
                return JsonResponse({'message': 'error proposition'}, status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse({'message': 'details was added successfully and proostion was added successfully'}, status=status.HTTP_204_NO_CONTENT)
        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Bad request'}, status=status.HTTP_400_BAD_REQUEST)


def sessions_filtred_list(request,page_number):
    if request.method == 'GET':
        code_session=request.GET.get("code_session")
        date=request.GET.get("date")
        critere=request.GET.get("critere")
        filter_conditions = Q()
        if code_session:
            filter_conditions &= Q(code_session=code_session)
        if date:
            filter_conditions &= Q(date=date)
        if critere:
            filter_conditions &= Q(critere=critere)
        results=EnteteSession.objects.filter(filter_conditions)[(int(page_number)-1)*page_size:(int(page_number)-1)*page_size+page_size+1]
        sessions_serializer = SessionSerializer(results, many=True)
        return JsonResponse(sessions_serializer.data, safe=False)

@api_view(['GET'])
def proposition_affichage(request,pk):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("SELECT  concat(e1.code_etab,'_',e2.code_etab) as ordre_trf,a.code_article_gen,d1.code_article_dem,a.code_barre,a.lib_taille,a.lib_couleur,e1.libelle as emet,e2.libelle as recep,p.qte_trf,d1.code_session,s.date,u.nom,p.statut from proposition p , etablissement e1, article a ,entete_session s,detaille_session d1,detaille_session d2,etablissement e2, user u where p.code_detaille_emet=d1.id_detaille and p.code_detaille_recep=d2.id_detaille and d1.code_session=s.code_session and d1.code_etab=e1.code_etab and d2.code_etab=e2.code_etab and a.code_article_dem=d1.code_article_dem and u.id_user=s.id_user and s.code_session= %s ORDER BY ordre_trf,d1.code_article_dem ", [pk])
            list_prop=cursor.fetchall()
        liste_avec_code_depot=[]
        props_avec_code_dpot=[]
        for prop in list_prop:
            id_etab=prop[0][0:prop[0].index('_')]
            print(id_etab)
            depots_emet=Stock.objects.filter(code_etab=id_etab).order_by('-stock_physique')
            #depots_emet.sort(key=lambda x: x[4], reverse=True)
            for dep in depots_emet:
                 global totale_trf_etab
                 totale_trf_etab = prop[8]
                 if totale_trf_etab>0:
                    if totale_trf_etab-dep.stock_physique>=0:
                        totale_trf_etab=totale_trf_etab-dep.stock_physique
                        liste_avec_code_depot =list(prop)
                        liste_avec_code_depot[8]=dep.stock_physique
                        liste_avec_code_depot.append(dep.code_depot)
                    else:
                        totale_trf_etab=0
                        liste_avec_code_depot = list(prop)
                        liste_avec_code_depot[8] = dep.stock_physique-totale_trf_etab
                        liste_avec_code_depot.append(dep.code_depot)
                    props_avec_code_dpot.append(liste_avec_code_depot)
        print('liste a verfier')
        print(props_avec_code_dpot)
        list_prop_json = [
            {
                "ordre_trf":item[0],
                "code_article_gen": item[1],
                "code_article_dem": item[2],
                "code_barre": item[3],
                "lib_taille": item[4],
                "lib_couleur": item[5],
                "emet": item[6],
                "recep": item[7],
                "qte_trf": item[8],
                "code_session": item[9],
                "date": item[10],
                "nom": item[11],
                "statut": item[12],
                "code_depot_emet": item[13]
            }
            for item in props_avec_code_dpot
        ]
        return JsonResponse(list_prop_json, safe=False)



