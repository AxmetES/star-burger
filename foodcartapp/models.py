from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from environs import Env
from geopy import distance
from phonenumber_field.modelfields import PhoneNumberField

env = Env()
env.read_env()


class CustomQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        for obj in self:
            obj.place.delete()
        super().delete(*args, **kwargs)


class Restaurant(models.Model):
    objects = CustomQuerySet.as_manager()

    name = models.CharField('название', max_length=50)
    address = models.CharField('адрес', max_length=100, blank=True)
    contact_phone = models.CharField('контактный телефон', max_length=50, blank=True)
    place = models.ForeignKey('Place', on_delete=models.CASCADE, null=True, blank=True, verbose_name='место на карте')

    def __str__(self):
        return self.name

    def get_coords(self):
        return (str(self.place.lat), str(self.place.lng))

    def delete(self, *args, **kwargs):
        place = Place.objects.filter(address=self.address)
        if place:
            place.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'


class ProductQuerySet(models.QuerySet):
    def available(self):
        return self.distinct().filter(menu_items__availability=True)


class ProductCategory(models.Model):
    name = models.CharField('название', max_length=50)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField('название', max_length=50, unique=True)
    category = models.ForeignKey(ProductCategory, null=True, blank=True, on_delete=models.SET_NULL,
                                 verbose_name='категория', related_name='products')
    price = models.DecimalField('цена', max_digits=8, decimal_places=2, db_index=True,
                                validators=[MinValueValidator(0)])
    image = models.ImageField('картинка')
    special_status = models.BooleanField('спец.предложение', default=False, db_index=True)
    description = models.TextField('описание', max_length=200, blank=True)

    objects = ProductQuerySet.as_manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items',
                                   verbose_name="ресторан")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='menu_items',
                                verbose_name='продукт')
    availability = models.BooleanField('в продаже', default=True, db_index=True)

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
            ]


class Order(models.Model):
    PROCESSED = 'PR'
    UNPROCESSED = 'UP'
    STATUS = [
        (PROCESSED, 'Обработанный'),
        (UNPROCESSED, 'Необработанный')
        ]
    CASH = 'CH'
    CART = 'CR'
    TRANSFER = 'TR'
    CRYPTOCURRENCY = 'CC'
    PAYMENT_METHOD = [
        (CASH, 'Наличными'),
        (CART, 'Банковская карта'),
        (TRANSFER, 'Электронный перевод'),
        (CRYPTOCURRENCY, 'Криптовалютный перевод'),
        ]

    objects = CustomQuerySet.as_manager()

    firstname = models.CharField(max_length=50, verbose_name='имя')
    lastname = models.CharField(max_length=50, verbose_name='фамилия')
    address = models.CharField(max_length=100, verbose_name='адрес')
    phonenumber = PhoneNumberField(verbose_name='номер телефона')
    registered_at = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='время рагистрации')
    updated_at = models.DateTimeField(verbose_name='время звонка', db_index=True, null=True)
    delivered_at = models.DateTimeField(verbose_name='время доставки', db_index=True, null=True)
    order_status = models.CharField(max_length=2, choices=STATUS, default=UNPROCESSED, db_index=True,
                                    verbose_name='статус заказа')
    payment_method = models.CharField(max_length=2, choices=PAYMENT_METHOD, db_index=True, blank=True,
                                      verbose_name='способ оплаты')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True, verbose_name='ресторан')
    comment = models.TextField(max_length=250, verbose_name='комментарии', blank=True)
    place = models.ForeignKey('Place', on_delete=models.CASCADE, related_name='orders', null=True, blank=True,
                              verbose_name='место на карте')

    def full_name(self):
        return '{} {}'.format(self.firstname, self.lastname)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def get_order_cost(self):
        return Order.objects.filter(pk=self.id).aggregate(order_cost=Sum('details__product_price'))['order_cost']

    def get_rest_rang(self):
        rest_range = []
        restaurants = Restaurant.objects.all()

        for rest in restaurants:
            if self.place:
                order_coords = self.place.get_coords()
                rest_coords = rest.get_coords()
                rest_distance = distance.distance(order_coords, rest_coords).km
                rest_range.append((rest.name, str(round(rest_distance, 3)) + ' km'))
                rest_range.sort(key=lambda x: x[1])

            else:
                rest_range.append(['No Geo API data'])

        rang_of_restrs = map(' - '.join, rest_range)
        return rang_of_restrs

    def delete(self, *args, **kwargs):
        place = Place.objects.filter(address=self.address)
        if place:
            place.delete()
        super(Order, self).delete(*args, **kwargs)


class OrderDetails(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='products',
                                verbose_name='продукт')
    quantity = models.IntegerField('количество', validators=[MinValueValidator(1), MaxValueValidator(100)])
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='details', verbose_name='заказ')
    product_price = models.DecimalField('сумма цен продукта', null=True, max_digits=8, decimal_places=2,
                                        validators=[MinValueValidator(Decimal('0.01'))])

    def __str__(self):
        return str(self.order)

    class Meta:
        verbose_name = 'Детали заказа'
        verbose_name_plural = 'Детали заказов'


class Place(models.Model):
    address = models.CharField(max_length=50, verbose_name='адресс')
    lat = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name='широта')
    lng = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, verbose_name='долгота')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='время рагистрации ')

    def __str__(self):
        return self.address

    def get_coords(self):
        return (str(self.lat), str(self.lng))

    class Meta:
        verbose_name = 'Место на карте'
        verbose_name_plural = 'Места на карте'
