# Generated by Django 2.1.5 on 2021-01-25 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0025_orderinfo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='influencerbase',
            name='centra_update_at',
        ),
        migrations.AddField(
            model_name='influencer',
            name='centra_update_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Centra Update At'),
        ),
    ]