# Generated by Django 2.1.5 on 2021-01-18 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0020_influencerbase_centra_update_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='influencerbase',
            name='centra_update_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Centra Update At'),
        ),
    ]
