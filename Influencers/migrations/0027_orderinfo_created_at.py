# Generated by Django 2.1.5 on 2021-01-29 16:52

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('Influencers', '0026_auto_20210125_0636'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderinfo',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Created At'),
            preserve_default=False,
        ),
    ]