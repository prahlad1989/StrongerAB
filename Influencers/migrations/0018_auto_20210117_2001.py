# Generated by Django 2.1.5 on 2021-01-17 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0017_auto_20210112_1721'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='influencer',
            name='is_old_order',
        ),
        migrations.AddField(
            model_name='influencer',
            name='is_old_record',
            field=models.BooleanField(default=False, null=True, verbose_name='Is Old Record?'),
        ),
    ]
