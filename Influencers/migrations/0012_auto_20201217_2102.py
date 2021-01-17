# Generated by Django 2.1.5 on 2020-12-17 21:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0011_auto_20201217_2043'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='influencerbase',
            options={'ordering': ['-created_at', '-updated_at']},
        ),
        migrations.AddIndex(
            model_name='influencer',
            index=models.Index(fields=['email', 'channel_username'], name='Influencers_email_7fa304_idx'),
        ),
        migrations.AddIndex(
            model_name='influencerbase',
            index=models.Index(fields=['-created_at', '-updated_at', 'created_by'], name='Influencers_created_2624e1_idx'),
        ),
    ]