# Generated by Django 2.1.5 on 2020-12-17 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0009_auto_20201215_0630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='influencer',
            name='channel_username',
            field=models.CharField(max_length=100, null=True, verbose_name='Instagram Username'),
        ),
        migrations.AlterField(
            model_name='influencer',
            name='date_of_promotion_on',
            field=models.DateField(null=True, verbose_name='Day of Promotion'),
        ),
        migrations.AlterField(
            model_name='influencer',
            name='last_contacted_on',
            field=models.DateField(null=True, verbose_name='Last Contacted Date'),
        ),
    ]
