# Generated by Django 2.1.5 on 2021-02-11 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0035_auto_20210211_1607'),
    ]

    operations = [
        migrations.AlterField(
            model_name='influencer',
            name='channel',
            field=models.CharField(max_length=200, null=True, verbose_name='Channel'),
        ),
    ]