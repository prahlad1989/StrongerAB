# Generated by Django 2.1.5 on 2021-01-20 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0022_auto_20210118_0909'),
    ]

    operations = [
        migrations.AddField(
            model_name='influencerbase',
            name='centra_orders_update_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Centra Orders Update At'),
        ),
        migrations.AlterField(
            model_name='influencer',
            name='revenue_click',
            field=models.FloatField(default=0, null=True, verbose_name='Revenue Qlik'),
        ),
    ]
