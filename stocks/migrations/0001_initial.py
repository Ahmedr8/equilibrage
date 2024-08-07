# Generated by Django 4.2.3 on 2024-02-27 22:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('code_article_dem', models.CharField(max_length=50)),
                ('code_etab', models.CharField(max_length=50)),
                ('code_barre', models.CharField(max_length=50)),
                ('stock_min', models.FloatField()),
                ('stock_physique', models.FloatField()),
                ('ventes', models.FloatField()),
                ('trecu', models.IntegerField(db_column='Trecu')),
                ('t_trf_recu', models.IntegerField(db_column='T_trf_recu')),
                ('t_trf_emis', models.IntegerField(db_column='T_trf_emis')),
                ('code_depot', models.CharField(max_length=50)),
                ('id_stock', models.AutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'stock',
                'managed': True,
                'unique_together': {('code_article_dem', 'code_depot')},
            },
        ),
    ]
