import json

from django.http import JsonResponse
from django.templatetags.static import static

from .models import Product, Order, OrderDetails
from rest_framework.decorators import api_view


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    data = request.data
    order, is_created = Order.objects.update_or_create(
        firstname=data['firstname'],
        lastname=data['lastname'],
        phone_number=data['phonenumber'],
        address=data['address']
    )

    product = Product.objects.filter(id=data['products'][0]['product'])
    print(product[0].price)
    for product_item in data['products']:
        order_details, is_created = OrderDetails.objects.update_or_create(
            product=Product.objects.filter(id=product_item['product'])[0],
            order=order,
            defaults={
                'quantity': product_item['quantity'],
                'product_price': Product.objects.filter(id=product_item['product'])[0].price * product_item['quantity']
            })
        if not is_created:
            order_details.quantity = order_details.quantity + product_item['quantity']
            order_details.product_price = float(order_details.product_price) + float((
                Product.objects.filter(id=product_item['product'])[0].price * product_item['quantity']
            ))
            order_details.save()
    return JsonResponse({})
