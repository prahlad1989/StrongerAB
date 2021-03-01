# Generated by Django 2.1.5 on 2021-02-22 06:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0041_auto_20210218_2335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='influencer',
            name='paid_or_unpaid',
            field=models.CharField(blank=True, choices=[('', ''), ('Paid', 'Paid'), ('Unpaid', 'Unpaid'), ('ÖK', 'ÖK')], default=None, max_length=10, null=True, verbose_name='Paid/Unpaid'),
        ),
    ]