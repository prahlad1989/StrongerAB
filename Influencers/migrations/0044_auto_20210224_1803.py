# Generated by Django 2.1.5 on 2021-02-24 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0043_auto_20210224_0958'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='influencer',
            name='last_contacted_on',
        ),
        migrations.AlterField(
            model_name='influencer',
            name='date_of_promotion_on',
            field=models.DateField(null=True, verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='influencer',
            name='is_influencer',
            field=models.CharField(choices=[('', ''), ('Prospect', 'Prospect'), ('Influencer', 'Influencer'), ('PR_', 'PR_'), ('Affiliate', 'Affiliate')], max_length=12, verbose_name='Influencer/Prospect'),
        ),
    ]
