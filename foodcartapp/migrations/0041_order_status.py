# Generated by Django 3.1.5 on 2021-02-05 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0040_auto_20210204_0610'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('PROCESSED', 'Processed'), ('UNPROCESSED', 'Unprocessed')], default='UP', max_length=11),
        ),
    ]