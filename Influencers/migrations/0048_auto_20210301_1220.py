# Generated by Django 2.1.5 on 2021-03-01 12:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0047_auto_20210228_1038'),
    ]

    operations = [
        migrations.RenameField(
            model_name='influencer',
            old_name='date_of_promotion_on',
            new_name='date_of_promotion_at',
        ),
    ]