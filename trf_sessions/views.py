from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from trf_sessions.models import EnteteSession,DetailleSession,Proposition
from stocks.models import Stock
from trf_sessions.serializers import SessionSerializer,DetailleSessionSerializer,PropositionSerializer
from django.db import IntegrityError
from django.db.models import Q
import json
from django.db import connection
from django.conf import settings
from articles.models import Article

page_size=settings.PAGINATION_PAGE_SIZE


@csrf_exempt
def sessions_list(request,page_number):
    if request.method == 'GET':
        sessions = EnteteSession.objects.all()[(int(page_number)-1)*page_size:(int(page_number)-1)*page_size+page_size]
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
def custom_sort_demande(element,best_seller):
    print(element)
    if best_seller in element[2]:
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
        crit= json_data.get('critere')
        articles_gen=[]
        print(articles)
        print("crittere",crit)
        if crit=="articles_dem":
            articles_gen=articles
            articles=[]
        etabs = json_data.get('etabs', [])
        prios = json_data.get('prios', [])
        stoock_min_value = json_data.get('stock_min')
        print("articles_gen:",articles_gen)
        print("articles:", articles)
        print("etabs:", etabs)
        print("prios:", prios)
        print(crit)
        print(stoock_min_value)
        d_session=[]
        d_sessionf=[]
        id_s=pk
        sql_query ="SELECT s.id_stock,s.code_article_dem,s.code_etab,e.priorite,e.type,SUM(s.stock_physique) as stock_physique,s.stock_min,s.ventes FROM stock s,depot d,etablissement e where s.code_depot=d.code_depot and d.code_etab=e.code_etab GROUP by s.ventes,e.priorite,s.stock_min,e.type,s.id_stock,s.code_article_dem,s.code_etab"
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
        if crit=="articles_dem":
            print("code article dem critere")
            propositions = []
            for article_gen in articles_gen:
                d_session = []
                d_sessionf = []
                print("article gen ",article_gen)
                sql_query_best_etab = "select a.code_article_gen,s.code_etab,sum(s.ventes) as su from stock s,article a where a.code_article_dem=s.code_article_dem and a.code_article_gen= %s group by a.code_article_gen,s.code_etab order by su desc"
                with connection.cursor() as cursor:
                    cursor.execute(sql_query_best_etab,[article_gen])
                    best_seller_etab_values= cursor.fetchone()
                    best_seller_etab_values_list=list(best_seller_etab_values)
                    best_seller_etab=best_seller_etab_values_list[1]
                    print("best seller is ",best_seller_etab)
                liste_article_gen = Article.objects.filter(code_article_gen=article_gen).values_list('code_article_dem',flat=True)
                articles=list(liste_article_gen)
                for i, details in enumerate(results):
                    # print(details)
                    details_instance = DetailleSession(code_session=id_s, code_article_dem=details[1],
                                                       code_etab=details[2], stock_physique=details[5],
                                                       stock_min=details[6])
                    if (details_instance.code_etab in etabs) and (details_instance.code_article_dem in articles):
                        aux_list = list(details)
                        aux_list[3] = prios[etabs.index(details[2])]
                        d_sessionf.append(aux_list)
                        d_session.append(details_instance)
                try:
                    DetailleSession.objects.bulk_create(d_session)
                except IntegrityError as e:
                    print(e)
                    return JsonResponse({'message': 'error dettailes sessions'}, status=status.HTTP_400_BAD_REQUEST)
                for code_article in articles:
                    offre = []
                    offre1 = []
                    demande = []
                    stock_min = int(stoock_min_value)
                    for details in d_sessionf:
                        if (details[1] == code_article):
                            if details[5] > stock_min and details[2]!=best_seller_etab:
                                details.append(details[5] - stock_min)
                                new_details = details
                                # setattr(details, 'val',details.stock_physique-details.stock_min )
                                offre1.append(new_details)
                            elif details[5] < stock_min:
                                details.append(stock_min - details[5])
                                new_details = details
                                if new_details[5] < 0:
                                    new_details[5] = 0
                                    new_details[8] = stock_min
                                # setattr(details, 'val', details.stock_min-details.stock_physique)
                                if new_details[5] != 0 or new_details[7] != 0 or details[2]==best_seller_etab:
                                    demande.append(new_details)
                    print("offre",offre1)
                    print("demande",demande)
                    offre1.sort(key=lambda x: (x[7]), reverse=False)
                    demande.sort(key=lambda x: (x[7], x[3]), reverse=True)
                    sorted_demands = demande
                    print(sorted_demands)
                    sorted_demands_list=[list(d) for d in sorted_demands]
                    demande = sorted(sorted_demands_list, key=lambda x: custom_sort_demande(x, best_seller_etab))
                    print('tri')
                    # offre = sorted(offre1, key=custom_sort_key)
                    list_list = [list(t) for t in offre1]
                    list_list_dem = [list(d) for d in demande]
                    offre = list_list
                    demande = list_list_dem
                    print("offre :",offre)
                    print("demande :",demande)
                    i = 0
                    k = 0
                    cpt_offre = 0
                    cpt_demande = 0
                    while offre and demande:
                        if offre[0][7] == 0 and k != 0:
                            print('here out')
                            id_emet = DetailleSession.objects.get(code_article_dem=offre[0][1], code_etab=offre[0][2],
                                                                  code_session=id_s)
                            id_recep = DetailleSession.objects.get(code_article_dem=demande[i][1],
                                                                   code_etab=demande[i][2], code_session=id_s)
                            prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                               code_detaille_recep=id_recep.id_detaille, qte_trf=1, statut="en cours",
                                               etat="non modifier")
                            offre[0][8] = offre[0][8] - 1
                            demande[i][8] = demande[i][8] - 1
                            if demande[i][8] == 0:
                                del demande[i]
                            else:
                                i = i + 1
                            if offre[0][8] == 0:
                                del offre[0]
                            if i == len(demande):
                                i = 0

                            propositions.append(prop)
                        else:
                            id_emet = DetailleSession.objects.get(code_article_dem=offre[cpt_offre][1],
                                                                  code_etab=offre[cpt_offre][2],
                                                                  code_session=id_s)
                            id_recep = DetailleSession.objects.get(code_article_dem=demande[cpt_demande][1],
                                                                   code_etab=demande[cpt_demande][2], code_session=id_s)
                            prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                               code_detaille_recep=id_recep.id_detaille, qte_trf=1, statut="en cours",
                                               etat="non modifier")
                            propositions.append(prop)
                            offre[cpt_offre][8] = offre[cpt_offre][8] - 1
                            demande[cpt_demande][8] = demande[cpt_demande][8] - 1
                            if demande[cpt_demande][8] == 0:
                                del demande[cpt_demande]
                            else:
                                cpt_demande = cpt_demande + 1
                            if offre[cpt_offre][8] == 0:
                                del offre[cpt_offre]
                            else:
                                cpt_offre = cpt_offre + 1
                            if cpt_demande == len(demande):
                                cpt_demande = 0
                            if cpt_offre == len(offre):
                                cpt_offre = 0
                                k = k + 1
                            print("proposition 1ere iteration", propositions)
                    if demande:
                        print('demande')
                        print(demande)
                        offre1 = []
                        for details in d_sessionf:
                            if (details[1] == code_article):
                                if details[5] >= stock_min:
                                    details.append(stock_min)
                                    new_details = details
                                    # setattr(details, 'val',details.stock_physique-details.stock_min )
                                    offre1.append(new_details)
                        offre1.sort(key=lambda x: (x[7]), reverse=False)
                        list_list = [list(t) for t in offre1]
                        offre = list_list
                        prop_verif = True
                        print("offre")
                        print(offre)
                        while offre and demande and prop_verif == True:
                            if offre[0][7] < demande[0][7]:
                                id_emet = DetailleSession.objects.get(code_article_dem=offre[0][1],
                                                                      code_etab=offre[0][2],
                                                                      code_session=id_s)
                                id_recep = DetailleSession.objects.get(code_article_dem=demande[0][1],
                                                                       code_etab=demande[0][2], code_session=id_s)
                                prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                                   code_detaille_recep=id_recep.id_detaille, qte_trf=1,
                                                   statut="en cours",
                                                   etat="non modifier")
                                propositions.append(prop)
                                offre[0][8] = offre[0][8] - 1
                                demande[0][8] = demande[0][8] - 1
                                if demande[0][8] == 0:
                                    del demande[0]
                                if offre[0][8] == 0:
                                    del offre[0]
                                print('offre del: ', offre)
                                print('demande del: ', demande)
                            else:
                                prop_verif = False
                            print('proposotions last iteration', propositions)
            print(propositions)
            try:
                Proposition.objects.bulk_create(propositions)
                return JsonResponse(
                    {'message': 'details was added successfully and proostion was added successfully'},
                    status=status.HTTP_204_NO_CONTENT)
            except IntegrityError as e:
                print(e)
                return JsonResponse({'message': 'error proposition'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            for i,details in enumerate(results):
                #print(details)
                details_instance=DetailleSession(code_session=id_s,code_article_dem=details[1],code_etab=details[2],stock_physique=details[5],stock_min=details[6])
                if (details_instance.code_article_dem in articles) and crit == "seul_emet":
                    aux_list = list(details)
                    if (details[4] == 'siege' and details[5] != 0) or (details[2] ==etabs[0] and details[5] == 0):
                        articles.remove(details[1])
                    else:
                        d_sessionf.append(aux_list)
                        d_session.append(details_instance)
                elif (details_instance.code_etab in etabs) and (details_instance.code_article_dem in articles):
                    aux_list=list(details)
                    aux_list[3]=prios[etabs.index(details[2])]
                    '''
                    if details[4]=='siege' and details[5]!=0 and crit=="moy_ventes":
                        articles.remove(details[1])
                    else:
                        d_sessionf.append(aux_list)
                        d_session.append(details_instance)
                    '''
                    d_sessionf.append(aux_list)
                    d_session.append(details_instance)
            try:

                print("detaill finale :",d_sessionf)
                try:
                    DetailleSession.objects.bulk_create(d_session)
                except IntegrityError as e:
                    print(e)
                    return JsonResponse({'message': 'error dettailes sessions'}, status=status.HTTP_400_BAD_REQUEST)
                propositions=[]
                if crit=="stock_min":
                    for code_article in articles:
                        offre=[]
                        offre1=[]
                        demande=[]
                        for details in d_sessionf:
                            if (details[1] == code_article):
                                if details[5] > details[6] :
                                    details.append(details[5]-details[6])
                                    new_details =details
                                    # setattr(details, 'val',details.stock_physique-details.stock_min )
                                    offre1.append(new_details)
                                elif details[5] < details[6]:
                                    details.append(details[6]-details[5])
                                    new_details =details
                                    #setattr(details, 'val', details.stock_min-details.stock_physique)
                                    demande.append(new_details)
                        print(offre1)
                        print(demande)
                        offre1.sort(key= lambda x:(x[3],x[8]), reverse=True)
                        demande.sort(key= lambda  x:(x[3],x[8]), reverse=True)
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
                            if offre[i][8] > demande[i][8]:
                                qte=demande[i][8]
                                prop=Proposition(code_detaille_emet=id_emet.id_detaille,code_detaille_recep=id_recep.id_detaille,qte_trf=qte,statut="en cours",etat="non modifier")
                                offre[i][8]=offre[i][8]-demande[i][8]
                                del demande[i]
                            elif offre[i][8] < demande[i][8]:
                                qte=offre[i][8]
                                prop=Proposition(code_detaille_emet=id_emet.id_detaille,code_detaille_recep=id_recep.id_detaille,qte_trf=qte,statut="en cours",etat="non modifier")
                                demande[i][8]=demande[i][8]-offre[i][8]
                                del offre[i]
                            else:
                                qte=offre[i][8]
                                prop=Proposition(code_detaille_emet=id_emet.id_detaille,code_detaille_recep=id_recep.id_detaille,qte_trf=qte,statut="en cours",etat="non modifier")
                                del offre[i]
                                del demande[i]
                            propositions.append(prop)
                elif crit=="moy_ventes":
                    print("moyenne des ventes")
                    for code_article in articles:
                        offre=[]
                        offre1=[]
                        demande=[]
                        stock_min=int(stoock_min_value)
                        for details in d_sessionf:
                            if (details[1] == code_article):
                                if details[5] > stock_min :
                                    details.append(details[5]-stock_min)
                                    new_details =details
                                    # setattr(details, 'val',details.stock_physique-details.stock_min )
                                    offre1.append(new_details)
                                elif details[5] < stock_min:
                                    details.append(stock_min-details[5])
                                    new_details =details
                                    if new_details[5]<0:
                                        new_details[5]=0
                                        new_details[8]=stock_min
                                    #setattr(details, 'val', details.stock_min-details.stock_physique)
                                    if new_details[5]!=0 or new_details[7]!=0:
                                        demande.append(new_details)
                        #print(offre1)
                        #print(demande)
                        offre1.sort(key= lambda x:(x[7]), reverse=False)
                        demande.sort(key= lambda  x:(x[7],x[3]), reverse=True)
                        print('tri')
                        # offre = sorted(offre1, key=custom_sort_key)
                        list_list=[list(t) for t in offre1]
                        list_list_dem=[list(d) for d in demande]
                        offre=list_list
                        demande=list_list_dem
                        #print(offre)
                        #print(demande)
                        i=0
                        k=0
                        cpt_offre=0
                        cpt_demande=0
                        while offre and demande :
                            if offre[0][7]==0 and k!=0:
                                #print('here out')
                                id_emet = DetailleSession.objects.get(code_article_dem=offre[0][1], code_etab=offre[0][2],
                                                                      code_session=id_s)
                                id_recep = DetailleSession.objects.get(code_article_dem=demande[i][1],
                                                                       code_etab=demande[i][2], code_session=id_s)
                                prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                                   code_detaille_recep=id_recep.id_detaille, qte_trf=1, statut="en cours",
                                                   etat="non modifier")
                                offre[0][8] = offre[0][8] - 1
                                demande[i][8] = demande[i][8] - 1
                                if demande[i][8] == 0:
                                    del demande[i]
                                else:
                                    i = i + 1
                                if offre[0][8] == 0:
                                    del offre[0]
                                if i == len(demande):
                                    i = 0


                                propositions.append(prop)
                            else:
                                id_emet = DetailleSession.objects.get(code_article_dem=offre[cpt_offre][1], code_etab=offre[cpt_offre][2],
                                                                      code_session=id_s)
                                id_recep = DetailleSession.objects.get(code_article_dem=demande[cpt_demande][1],
                                                                       code_etab=demande[cpt_demande][2], code_session=id_s)
                                prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                                   code_detaille_recep=id_recep.id_detaille, qte_trf=1, statut="en cours",
                                                   etat="non modifier")
                                propositions.append(prop)
                                offre[cpt_offre][8] = offre[cpt_offre][8] - 1
                                demande[cpt_demande][8] = demande[cpt_demande][8] - 1
                                if demande[cpt_demande][8] == 0:
                                    del demande[cpt_demande]
                                else:
                                    cpt_demande = cpt_demande + 1
                                if offre[cpt_offre][8] == 0:
                                    del offre[cpt_offre]
                                else:
                                    cpt_offre=cpt_offre+1
                                if cpt_demande == len(demande):
                                    cpt_demande = 0
                                if cpt_offre==len(offre):
                                    cpt_offre=0
                                    k=k+1
                                #print("proposition 1ere iteration",propositions)
                        if demande:
                            #print('demande')
                            #print(demande)
                            offre1 = []
                            for details in d_sessionf:
                                if (details[1] == code_article):
                                    if details[5] >= stock_min:
                                        details.append(stock_min)
                                        new_details = details
                                        # setattr(details, 'val',details.stock_physique-details.stock_min )
                                        offre1.append(new_details)
                            offre1.sort(key=lambda x: (x[7]), reverse=False)
                            list_list = [list(t) for t in offre1]
                            offre = list_list
                            prop_verif=True
                            #print("offre")
                            #print(offre)
                            while offre and demande and prop_verif==True:
                                if offre[0][7]<demande[0][7]:
                                    id_emet = DetailleSession.objects.get(code_article_dem=offre[0][1],
                                                                          code_etab=offre[0][2],
                                                                          code_session=id_s)
                                    id_recep = DetailleSession.objects.get(code_article_dem=demande[0][1],
                                                                           code_etab=demande[0][2], code_session=id_s)
                                    prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                                       code_detaille_recep=id_recep.id_detaille, qte_trf=1,
                                                       statut="en cours",
                                                       etat="non modifier")
                                    propositions.append(prop)
                                    offre[0][8] = offre[0][8] - 1
                                    demande[0][8] = demande[0][8] - 1
                                    if demande[0][8] == 0:
                                        del demande[0]
                                    if offre[0][8] == 0:
                                        del offre[0]
                                    #print('offre del: ', offre)
                                    #print('demande del: ', demande)
                                else:
                                    prop_verif=False
                                #print('proposotions last iteration',propositions)
                elif crit=='seul_emet':
                    for code_article in articles:
                        demande=[]
                        offre=[]
                        stock_min = int(stoock_min_value)
                        for details in d_sessionf:
                            if (details[1] == code_article):
                                if details[5] > 0 and (details[2] == etabs[0]):
                                    details.append(details[5])
                                    new_details = details
                                    # setattr(details, 'val',details.stock_physique-details.stock_min )
                                    offre.append(new_details)
                                elif details[5] < stock_min:
                                    details.append(stock_min - details[5])
                                    new_details = details
                                    if new_details[5] < 0:
                                        new_details[5] = 0
                                        new_details[8] = stock_min
                                    # setattr(details, 'val', details.stock_min-details.stock_physique)
                                    if new_details[7] != 0 and new_details[2]!=etabs[0]:
                                        demande.append(new_details)
                        print(demande)
                        demande.sort(key= lambda  x:(x[7],x[3]), reverse=True)
                        list_list_dem=[list(d) for d in demande]
                        demande=list_list_dem
                        print("offre",offre)
                        print("demannde",demande)
                        cpt_demande=0
                        while offre and demande:
                            id_emet = DetailleSession.objects.get(code_article_dem=offre[0][1],
                                                                  code_etab=offre[0][2],
                                                                  code_session=id_s)
                            id_recep = DetailleSession.objects.get(code_article_dem=demande[cpt_demande][1],
                                                                   code_etab=demande[cpt_demande][2], code_session=id_s)
                            prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                               code_detaille_recep=id_recep.id_detaille, qte_trf=1, statut="en cours",
                                               etat="non modifier")
                            propositions.append(prop)
                            offre[0][8] = offre[0][8] - 1
                            demande[cpt_demande][8] = demande[cpt_demande][8] - 1
                            if demande[cpt_demande][8] == 0:
                                del demande[cpt_demande]
                            else:
                                cpt_demande = cpt_demande + 1
                            if offre[0][8] == 0:
                                del offre[0]
                            if cpt_demande == len(demande):
                                cpt_demande = 0
                #print(propositions)
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
        results=EnteteSession.objects.filter(filter_conditions)[(int(page_number)-1)*page_size:(int(page_number)-1)*page_size+page_size]
        sessions_serializer = SessionSerializer(results, many=True)
        return JsonResponse(sessions_serializer.data, safe=False)

@api_view(['GET'])
def proposition_affichage(request,pk):
    global totale_trf_etab
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("SELECT  concat(e1.code_etab,'_',e2.code_etab) as ordre_trf,a.code_article_gen,d1.code_article_dem,a.code_barre,a.lib_taille,a.lib_couleur,e1.libelle as emet,e2.libelle as recep,p.qte_trf,d1.code_session,s.date,s.id_user,p.statut from proposition p , etablissement e1, article a ,entete_session s,detaille_session d1,detaille_session d2,etablissement e2 where p.code_detaille_emet=d1.id_detaille and p.code_detaille_recep=d2.id_detaille and d1.code_session=s.code_session and d1.code_etab=e1.code_etab and d2.code_etab=e2.code_etab and a.code_article_dem=d1.code_article_dem and s.code_session= %s ORDER BY ordre_trf,d1.code_article_dem ", [pk])
            list_prop=cursor.fetchall()
        props_avec_code_dpot=[]
        code_etabs_emet_liste=[]
        depots_emet_liste=[]
        for prop in list_prop:
            id_etab=prop[0][0:prop[0].index('_')]
            #print(id_etab)
            if id_etab not in code_etabs_emet_liste:
                code_etabs_emet_liste.append(id_etab)
                depots_emet=Stock.objects.filter(code_etab=id_etab).order_by('-stock_physique')
                depots_emet_liste.append(depots_emet)
            else:
                for item in depots_emet_liste:
                    if item[0].code_etab == id_etab:
                        depots_emet=item

            totale_trf_etab = prop[8]
            #depots_emet.sort(key=lambda x: x[4], reverse=True)
            for dep in depots_emet:
                 if totale_trf_etab>0 and dep.code_article_dem==prop[2]:
                    if totale_trf_etab-dep.stock_physique>=0:
                        totale_trf_etab=totale_trf_etab-dep.stock_physique
                        liste_avec_code_depot =list(prop)
                        liste_avec_code_depot[8]=dep.stock_physique
                        dep.stock_physique =0
                        liste_avec_code_depot.append(dep.code_depot)
                    else:
                        liste_avec_code_depot = list(prop)
                        liste_avec_code_depot[8] =totale_trf_etab
                        dep.stock_physique=dep.stock_physique-totale_trf_etab
                        liste_avec_code_depot.append(dep.code_depot)
                        totale_trf_etab = 0
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


@api_view(['DELETE'])
def delete_all_records(request):
    try:
        records_to_delete = EnteteSession.objects.all()
        records_to_delete.delete()

        return JsonResponse({'message': 'All Sessions deleted successfully!'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

