from django.urls import path,re_path

from articles import views

urlpatterns = [
    re_path(r'^page=(?P<page_number>\d+)$', views.articles_list),
    re_path(r'^filtred/page=(?P<page_number>\d+)$', views.articles_filtred_list),
    re_path(r'^filtred_exist/page=(?P<page_number>\d+)$', views.articles_filtred_list_exist),
    re_path(r'^delete', views.delete_all_records),
    re_path(r'^api/famille-options', views.get_famille_options),
    re_path(r'^api/couleur-options', views.get_couleur_options),
    re_path(r'^api/besoin-options', views.get_besoin_options),
    re_path(r'^api/grand-famille-options', views.get_grand_famille_options),
    re_path(r'^generique/page=(?P<page_number>\d+)$', views.articles_gen_list),
    re_path(r'^generique/filtred/page=(?P<page_number>\d+)$', views.articles_gen_filtred_list),
    re_path(r'^filtred', views.articles_filtred_list_without_pagination),
    re_path(r'^(?P<pk>\w+)$', views.article_detail),
    re_path(r'^api/sous-famille-options', views.get_sous_famille_options),
    re_path(r'^api/group-options', views.get_group_options),
    re_path(r'^api/materials-options', views.get_materials_options),
    re_path(r'^api/providers-options', views.get_providers_options),   #fournisseur
    re_path(r'^api/theme-options', views.get_theme_options),
    re_path(r'^api/marque-options', views.get_marque_options),
    re_path(r'^api/section-options', views.get_section_options),
    re_path(r'^api/collection-options', views.get_collection_options),




]