# Generated by Django 3.1.5 on 2021-02-06 04:05

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0048_order_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('CH', 'Наличными'), ('CR', 'Банковская карта'), ('TR', 'Электронный перевод'), ('CC', 'Криптовалютный перевод')], max_length=2, verbose_name='способ оплаты'),
        ),
        migrations.AlterField(
            model_name='order',
            name='registrated_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='время рагистрации'),
        ),
    ]