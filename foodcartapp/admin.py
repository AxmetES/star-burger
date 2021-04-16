import requests
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from environs import Env

from .fetch_coordinates import fetch_coordinates
from .models import Product, Order, OrderDetails, Place
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem

env = Env()
env.read_env()


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
        ]
    list_display = [
        'name',
        'address',
        'contact_phone',
        ]
    inlines = [
        RestaurantMenuItemInline
        ]

    def save_model(self, request, obj, form, change):
        apikey = env.str('GEO_API_KEY')
        try:
            lng, lat = fetch_coordinates(apikey, obj.address)
        except requests.exceptions.RequestException as e:
            print(e)

        if obj.place:
            address = obj.place.address
        else:
            address = obj.address
        place, is_created = Place.objects.get_or_create(address=address,
                                                        defaults={'lat': lat, 'lng': lng})
        if not is_created:
            place = obj.place
            place.address = obj.address
            place.lat = lat
            place.lng = lng
            place.save()
        else:
            obj.place = place
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
        ]
    list_display_links = [
        'name',
        ]
    list_filter = [
        'category',
        ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
        ]

    inlines = [
        RestaurantMenuItemInline
        ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
                ]
            }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
                ],
            'classes': [
                'wide'
                ],
            }),
        )

    readonly_fields = [
        'get_image_preview',
        ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
            }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" height="200"/>', url=obj.image.url)

    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" height="50"/></a>', edit_url=edit_url,
                           src=obj.image.url)

    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class DetailsInline(admin.TabularInline):
    model = OrderDetails
    readonly_fields = ['product_price']


@admin.register(OrderDetails)
class OrderDetailsAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'order')
    readonly_fields = ['product_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    search_fields = ["firstname__startswith"]
    list_filter = ['order_status']
    list_display = ['full_name', 'address', 'phonenumber']
    readonly_fields = ('registered_at',)
    inlines = [
        DetailsInline
        ]

    def response_post_save_change(self, request, obj):
        res = super().response_post_save_change(request, obj)
        if "next" in request.GET:
            return HttpResponseRedirect(reverse('restaurateur:view_orders'))
        else:
            return res

    def save_model(self, request, obj, form, change):
        apikey = env.str('GEO_API_KEY')
        try:
            lng, lat = fetch_coordinates(apikey, obj.address)
        except requests.exceptions.RequestException as e:
            print(e)

        if obj.place:
            address = obj.place.address
        else:
            address = obj.address
        place, is_created = Place.objects.get_or_create(address=address,
                                                        defaults={'lat': lat, 'lng': lng})
        if not is_created:
            place = obj.place
            place.address = obj.address
            place.lat = lat
            place.lng = lng
            place.save()

        else:
            obj.place = place
        super().save_model(request, obj, form, change)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['address', 'lat', 'lng']
    readonly_fields = ['created_at']

    def save_model(self, request, obj, form, change):
        apikey = env.str('GEO_API_KEY')
        try:
            lng, lat = fetch_coordinates(apikey=apikey, place=obj.address)
            obj.lng = lng
            obj.lat = lat

        except requests.exceptions.RequestException as e:
            print(e)
        super(PlaceAdmin, self).save_model(request, obj, form, change)
