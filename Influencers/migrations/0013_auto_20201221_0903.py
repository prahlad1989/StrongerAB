# Generated by Django 2.1.5 on 2020-12-21 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0012_auto_20201217_2102'),
    ]

    operations = [
        migrations.AlterField(
            model_name='influencer',
            name='order_num',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Order Number'),
        ),
    ]