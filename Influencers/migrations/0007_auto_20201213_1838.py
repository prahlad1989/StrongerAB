# Generated by Django 2.1.5 on 2020-12-13 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0006_auto_20201213_1827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='influencer',
            name='is_answered',
            field=models.CharField(blank=True, choices=[('', ''), ('Yes', 'Yes'), ('No', 'No')], max_length=5, null=True, verbose_name='Answered'),
        ),
        migrations.AlterField(
            model_name='influencer',
            name='paid_or_unpaid',
            field=models.CharField(blank=True, choices=[('', ''), ('Paid', 'Paid'), ('Unpaid', 'Unpaid'), ('OK', 'OK')], default=None, max_length=10, null=True, verbose_name='Paid/UnPaid'),
        ),
    ]
