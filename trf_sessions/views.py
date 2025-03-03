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
import datetime
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
        DetailleSession.objects.filter(code_session=pk).delete()
        return JsonResponse({'message': 'session was deleted successfully!'}, status=status.HTTP_200_OK)
    elif request.method =='PUT':
        session_data = JSONParser().parse(request)
        session_serializer = SessionSerializer(session, data=session_data)
        if session_serializer.is_valid():
            session_serializer.save()
            return JsonResponse(session_serializer.data)
        return JsonResponse(session_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def custom_sort_key(element):
    #print(element)
    if "siege" in element[4]:
        #print('siege')
        return 0
    else:
        return 1
def custom_sort_demande(element,best_seller):
    #print(element)
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
            return JsonResponse({'message': 'Invalid JSON data.'}, status=400)
        articles = json_data.get('articles', [])
        crit= json_data.get('critere')
        articles_gen=[]
        #print(articles)
        #print("crittere",crit)
        if crit=="articles_dem":
            articles_gen=articles
            articles=[]
        etabs = json_data.get('etabs', [])
        prios = json_data.get('prios', [])
        stoock_min_value = json_data.get('stock_min')
        #print("articles_gen:",articles_gen)
        #print("articles:", articles)
        #print("etabs:", etabs)
        print("prios:", prios)
        #print(crit)
        #print(stoock_min_value)
        d_session=[]
        d_sessionf=[]
        id_s=pk

        #------------------------------existe-----------------------------------------------
        if crit == "exist":
            recepteur_number = json_data.get('recepteur_number')
            start_date = json_data.get('start_date')
            end_date = json_data.get('end_date')
            print(start_date)
            print(end_date)
            listes_article_couleur ={}
            for i,article in enumerate(articles):
                tmp=article
                tmp_code_article=tmp[0:tmp.index(" ")]
                tmp=tmp.replace(" ","")
                articles[i] = f"{tmp_code_article}            {tmp[len(tmp_code_article):(len(tmp_code_article)+6)]}         {tmp[len(tmp)-1]}"
                article=f"{tmp_code_article}            {tmp[len(tmp_code_article):(len(tmp_code_article)+6)]}         {tmp[len(tmp)-1]}"
                if listes_article_couleur.get(tmp_code_article+tmp[(len(tmp_code_article)+3):(len(tmp_code_article)+6)])==None:
                    listes_article_couleur[tmp_code_article+tmp[(len(tmp_code_article)+3):(len(tmp_code_article)+6)]] = [article]
                else:
                    listes_article_couleur[tmp_code_article+tmp[len(tmp_code_article)+3:len(tmp_code_article)+6]] = listes_article_couleur[tmp_code_article+tmp[len(tmp_code_article)+3:len(tmp_code_article)+6]]+[article]
            print(listes_article_couleur)
            etabs_placeholders = ",".join(["%s"] * len(etabs))
            articles_placeholders = ",".join(["%s"] * len(articles))
            sql_query2 = f"""
                SELECT s.id_stock, s.code_article_dem, s.code_etab, e.priorite, e.type, 
                       SUM(s.stock_physique+s.T_trf_recu) AS stock_physique, s.stock_min
                FROM stock s
                JOIN depot d ON s.code_depot = d.code_depot
                JOIN etablissement e ON d.code_etab = e.code_etab
                WHERE e.code_etab IN ({etabs_placeholders})
                  AND s.code_article_dem IN ({articles_placeholders})
                GROUP BY e.priorite, s.stock_min, e.type, s.id_stock, s.code_article_dem, s.code_etab
            """

            sql_query_emet_prop = f"""select SUM(p.qte_trf) as qte_trf_emet,d1.code_etab as etab_emet,d1.code_article_dem 
                from proposition p,entete_session es,detaille_session d1
                where p.code_detaille_emet=d1.id_detaille and d1.code_session=es.code_session and es.date= %s
                and d1.code_etab IN ({etabs_placeholders})
                and d1.code_article_dem IN ({articles_placeholders})
                group by d1.code_etab,d1.code_article_dem"""

            sql_query_recep_prop = f"""select SUM(p.qte_trf) as qte_trf_recu,d2.code_etab as etab_emet,d2.code_article_dem 
                from proposition p,entete_session es,detaille_session d2
                where p.code_detaille_recep=d2.id_detaille and d2.code_session=es.code_session and es.date= %s
                and d2.code_etab IN ({etabs_placeholders})
                and d2.code_article_dem IN ({articles_placeholders})
                group by d2.code_etab,d2.code_article_dem"""
            with connection.cursor() as cursor:
                params2 = etabs + articles
                cursor.execute(sql_query2, params2)
                stock_results = cursor.fetchall()
                today = datetime.date.today()
                params3 = [today]+etabs + articles
                cursor.execute(sql_query_emet_prop, params3)
                emet_prop = cursor.fetchall()
                emet_dict = {(row[1], row[2]): row[0] for row in emet_prop}
                cursor.execute(sql_query_recep_prop, params3)
                recep_prop = cursor.fetchall()
                recep_dict = {(row[1], row[2]): row[0] for row in recep_prop}
            print(today)
            print(emet_dict)
            print(recep_dict)
            for i, details in enumerate(stock_results):
                search_value = (details[2],details[1])
                if search_value in emet_dict:
                    stock=details[5]-emet_dict[search_value]
                elif search_value in recep_dict :
                    stock = details[5] + recep_dict[search_value]
                else:
                    stock=details[5]
                details_instance = DetailleSession(code_session=id_s, code_article_dem=details[1],
                                                   code_etab=details[2], stock_physique=stock,
                                                   stock_min=details[6])
                aux_list = list(details)
                aux_list[3] = prios[etabs.index(details[2])]
                print(aux_list[2],' prio=',aux_list[3])
                aux_list[5]=stock
                if (details[4] == 'SIE' and stock != 0):
                    articles.remove(details[1])
                else:
                    d_sessionf.append(aux_list)
                    d_session.append(details_instance)
            try:
                DetailleSession.objects.bulk_create(d_session)
            except IntegrityError as e:
                print(e)
                return JsonResponse({'message': 'error details sessions'}, status=status.HTTP_400_BAD_REQUEST)
            propositions = []
            for key, value in listes_article_couleur.items():
                print("working on article couleur ",key,"----------------------------------")
                etabs_placeholders = ",".join(["%s"] * len(etabs))
                query = f"""
                        SELECT SUM(qte) AS totale_ventes, code_etab
                        FROM ventes
                        WHERE date_ventes <= %s
                        AND date_ventes >= %s
                        AND code_etab IN ({etabs_placeholders})
                        AND code_article LIKE %s
                        GROUP BY code_etab
                        ORDER BY totale_ventes DESC
                    """
                if(len(key)==9):
                    ch=f"{key[0:6]}            ___{key[6:9]}%"
                else:
                    ch=f"{key[0:5]}             ___{key[5:9]}%"
                code_article_prefix_like = ch
                print(code_article_prefix_like)
                with connection.cursor() as cursor:
                    params = [end_date, start_date] + etabs + [code_article_prefix_like]
                    cursor.execute(query,params)
                    ventes_results_list = cursor.fetchall()
                ventes_results_dict = {row[1]: [row[0],0] for row in ventes_results_list}
                print(ventes_results_dict)
                emmeteur = []
                recepteur = []
                for cle in ventes_results_dict.keys():
                    if (recepteur_number > 0):
                        recepteur.append(cle)
                        recepteur_number = recepteur_number - 1
                    else:
                        emmeteur.append(cle)
                for article_dim in value:
                    details_emmeteur = []
                    details_recepteur = []
                    for details in d_sessionf:
                        if (details[1] == article_dim):
                            if (details[2] in recepteur and details[5] < details[6]):
                                ventes_results_dict[details[2]][1] = ventes_results_dict[details[2]][1] + details[5]
                                details.append(ventes_results_dict[details[2]])
                                details.append(details[6] - details[5])
                                details_recepteur.append(details)
                            elif (details[2] in emmeteur and details[5] > 0):
                                ventes_results_dict[details[2]][1] = ventes_results_dict[details[2]][1] + details[5]
                                details.append(ventes_results_dict[details[2]])
                                details.append(details[5])
                                details_emmeteur.append(details)
                    details_emmeteur.sort(key=lambda x: (x[7][0], -x[3]), reverse=False)
                    details_recepteur.sort(key=lambda x: (x[7][0], -x[3]), reverse=True)
                    list_list = [list(t) for t in details_emmeteur]
                    list_list_dem = [list(d) for d in details_recepteur]
                    offre = list_list
                    demande = list_list_dem
                    i = 0
                    print("offre = ",offre)
                    print("demande =",demande)
                    while offre and demande:
                        id_emet = DetailleSession.objects.get(code_article_dem=offre[i][1], code_etab=offre[i][2],
                                                              code_session=id_s)
                        id_recep = DetailleSession.objects.get(code_article_dem=demande[i][1],
                                                               code_etab=demande[i][2], code_session=id_s)
                        if offre[i][8] > demande[i][8]:
                            qte = demande[i][8]
                            demande[i][5]=demande[i][5] + qte
                            offre[i][5]=offre[i][5] - qte
                            ventes_results_dict[offre[i][2]][1]=ventes_results_dict[offre[i][2]][1]-qte
                            ventes_results_dict[demande[i][2]][1] = ventes_results_dict[demande[i][2]][1] + qte
                            prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                               code_detaille_recep=id_recep.id_detaille, qte_trf=qte,
                                               statut="en cours", etat="non modifier",stock_recep_sera=demande[i][5],stock_emet_sera=offre[i][5]
                                               ,stock_recep_sera_couleur=demande[i][7][1],stock_emet_sera_couleur=offre[i][7][1])
                            offre[i][8] = offre[i][8] - demande[i][8]
                            del demande[i]
                        elif offre[i][8] < demande[i][8]:
                            qte = offre[i][8]
                            demande[i][5] = demande[i][5] + qte
                            offre[i][5] = offre[i][5] - qte
                            ventes_results_dict[offre[i][2]][1] = ventes_results_dict[offre[i][2]][1] - qte
                            ventes_results_dict[demande[i][2]][1] = ventes_results_dict[demande[i][2]][1] + qte
                            prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                               code_detaille_recep=id_recep.id_detaille, qte_trf=qte,
                                               statut="en cours", etat="non modifier",stock_recep_sera=demande[i][5],stock_emet_sera=offre[i][5]
                                               ,stock_recep_sera_couleur=demande[i][7][1],stock_emet_sera_couleur=offre[i][7][1])
                            demande[i][8] = demande[i][8] - offre[i][8]
                            del offre[i]
                        else:
                            qte = offre[i][8]
                            demande[i][5] = demande[i][5] + qte
                            offre[i][5] = offre[i][5] - qte
                            ventes_results_dict[offre[i][2]][1] = ventes_results_dict[offre[i][2]][1] - qte
                            ventes_results_dict[demande[i][2]][1] = ventes_results_dict[demande[i][2]][1] + qte
                            prop = Proposition(code_detaille_emet=id_emet.id_detaille,
                                               code_detaille_recep=id_recep.id_detaille, qte_trf=qte,
                                               statut="en cours", etat="non modifier",stock_recep_sera=demande[i][5],stock_emet_sera=offre[i][5]
                                               ,stock_recep_sera_couleur=demande[i][7][1],stock_emet_sera_couleur=offre[i][7][1])
                            del offre[i]
                            del demande[i]
                        propositions.append(prop)
                    #print(ventes_results_dict)
            try:
                print(propositions)
                Proposition.objects.bulk_create(propositions)
            except IntegrityError as e:
                # print(e)
                return JsonResponse({'message': 'error proposition'}, status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse({'message': 'propositions was added successfully'}, status=status.HTTP_200_OK)

                    

        # ------------------------------existe-----------------------------------------------
        sql_query ="SELECT s.id_stock,s.code_article_dem,s.code_etab,e.priorite,e.type,SUM(s.stock_physique) as stock_physique,s.stock_min,s.ventes FROM stock s,depot d,etablissement e where s.code_depot=d.code_depot and d.code_etab=e.code_etab GROUP by s.ventes,e.priorite,s.stock_min,e.type,s.id_stock,s.code_article_dem,s.code_etab"
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
        if crit=="articles_dem":
            #print("code article dem critere")
            propositions = []
            for article_gen in articles_gen:
                d_session = []
                d_sessionf = []
                #print("article gen ",article_gen)
                sql_query_best_etab = "select a.code_article_gen,s.code_etab,sum(s.ventes) as su from stock s,article a where a.code_article_dem=s.code_article_dem and a.code_article_gen= %s group by a.code_article_gen,s.code_etab order by su desc"
                with connection.cursor() as cursor:
                    cursor.execute(sql_query_best_etab,[article_gen])
                    best_seller_etab_values= cursor.fetchone()
                    best_seller_etab_values_list=list(best_seller_etab_values)
                    best_seller_etab=best_seller_etab_values_list[1]
                    #print("best seller is ",best_seller_etab)
                liste_article_gen = Article.objects.filter(code_article_gen=article_gen).values_list('code_article_dem',flat=True)
                articles=list(liste_article_gen)
                for i, details in enumerate(results):
                    # #print(details)
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
                    #print(e)
                    return JsonResponse({'message': 'error details sessions'}, status=status.HTTP_400_BAD_REQUEST)
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
                    #print("offre",offre1)
                    #print("demande",demande)
                    offre1.sort(key=lambda x: (x[7]), reverse=False)
                    demande.sort(key=lambda x: (x[7], x[3]), reverse=True)
                    sorted_demands = demande
                    #print(sorted_demands)
                    sorted_demands_list=[list(d) for d in sorted_demands]
                    demande = sorted(sorted_demands_list, key=lambda x: custom_sort_demande(x, best_seller_etab))
                    #print('tri')
                    # offre = sorted(offre1, key=custom_sort_key)
                    list_list = [list(t) for t in offre1]
                    list_list_dem = [list(d) for d in demande]
                    offre = list_list
                    demande = list_list_dem
                    #print("offre :",offre)
                    #print("demande :",demande)
                    i = 0
                    k = 0
                    cpt_offre = 0
                    cpt_demande = 0
                    while offre and demande:
                        if offre[0][7] == 0 and k != 0:
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
                            #print("proposition 1ere iteration", propositions)
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
                        prop_verif = True
                        #print("offre")
                        #print(offre)
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
                                #print('offre del: ', offre)
                                #print('demande del: ', demande)
                            else:
                                prop_verif = False
                            #print('proposotions last iteration', propositions)
            #print(propositions)
            try:
                Proposition.objects.bulk_create(propositions)
                return JsonResponse(
                    {'message': 'proostion was added successfully'},
                    status=status.HTTP_200_OK)
            except IntegrityError as e:
                #print(e)
                return JsonResponse({'message': 'error proposition'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            for i,details in enumerate(results):
                ##print(details)
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

                #print("detaill finale :",d_sessionf)
                try:
                    DetailleSession.objects.bulk_create(d_session)
                except IntegrityError as e:
                    #print(e)
                    return JsonResponse({'message': 'error details sessions'}, status=status.HTTP_400_BAD_REQUEST)
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
                        #print(offre1)
                        #print(demande)
                        offre1.sort(key= lambda x:(x[3],x[8]), reverse=True)
                        demande.sort(key= lambda  x:(x[3],x[8]), reverse=True)
                        #print('tri')
                        # offre = sorted(offre1, key=custom_sort_key)
                        list_list=[list(t) for t in offre1]
                        list_list_dem=[list(d) for d in demande]
                        offre=list_list
                        demande=list_list_dem
                        #print(offre)
                        #print(demande)
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
                    #print("moyenne des ventes")
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
                        ##print(offre1)
                        ##print(demande)
                        offre1.sort(key= lambda x:(x[7]), reverse=False)
                        demande.sort(key= lambda  x:(x[7],x[3]), reverse=True)
                        #print('tri')
                        # offre = sorted(offre1, key=custom_sort_key)
                        list_list=[list(t) for t in offre1]
                        list_list_dem=[list(d) for d in demande]
                        offre=list_list
                        demande=list_list_dem
                        #print('offre',offre)
                        #print('demande',demande)
                        i=0
                        k=0
                        cpt_offre=0
                        cpt_demande=0
                        while offre and demande :
                            if offre[0][7]<=0 and k!=0:
                                #print('2 eme iteration')
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
                                #print("2 eme iteration",propositions)
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
                            #print('demande en 3 iteration',demande)
                            offre1 = []
                            for details in d_sessionf:
                                if (details[1] == code_article):
                                    if details[5] >= stock_min:
                                        details.append(stock_min)
                                        new_details = details
                                        new_details[8]=stock_min
                                        # setattr(details, 'val',details.stock_physique-details.stock_min )
                                        offre1.append(new_details)
                            offre1.sort(key=lambda x: (x[7]), reverse=False)
                            list_list = [list(t) for t in offre1]
                            offre = list_list
                            prop_verif=True
                            ##print("offre")
                            #print('offre 3 eme iteration',offre)
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
                                    ##print('offre del: ', offre)
                                    ##print('demande del: ', demande)
                                else:
                                    prop_verif=False
                            #print('proposotions',propositions)

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
                        #print(demande)
                        demande.sort(key= lambda  x:(x[7],x[3]), reverse=True)
                        list_list_dem=[list(d) for d in demande]
                        demande=list_list_dem
                        #print("offre",offre)
                        #print("demannde",demande)
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
                    #print(e)
                    return JsonResponse({'message': 'error proposition'}, status=status.HTTP_400_BAD_REQUEST)
                return JsonResponse({'message':'propositions was added successfully'}, status=status.HTTP_200_OK)
            except IntegrityError as e:
                #print(e)
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
            cursor.execute("SELECT  concat(e1.code_etab,'_',e2.code_etab) as ordre_trf,a.code_article_gen,d1.code_article_dem,a.code_barre,a.lib_taille,a.lib_couleur,e1.libelle as emet,e2.libelle as recep,p.qte_trf,d1.code_session,s.date,s.id_user,p.statut,e2.code_etab,p.stock_recep_sera,p.stock_emet_sera,p.stock_recep_sera_couleur,p.stock_emet_sera_couleur from proposition p , etablissement e1, article a ,entete_session s,detaille_session d1,detaille_session d2,etablissement e2 where p.code_detaille_emet=d1.id_detaille and p.code_detaille_recep=d2.id_detaille and d1.code_session=s.code_session and d1.code_etab=e1.code_etab and d2.code_etab=e2.code_etab and a.code_article_dem=d1.code_article_dem and s.code_session= %s ORDER BY p.code_prop ", [pk])
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
        #print('liste a verfier')
        #print(props_avec_code_dpot)
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
                "code_etab_recep": item[13],
                "stock_recep_sera": item[14],
                "stock_emet_sera": item[15],
                "stock_emet_sera_couleur": item[17],
                "stock_recep_sera_couleur": item[16],
                "code_depot_emet": item[18]
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

