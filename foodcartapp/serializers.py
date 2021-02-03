from rest_framework.serializers import ModelSerializer

from foodcartapp.models import Order, OrderDetails


class OrderDetailsSerializer(ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = ('product', 'quantity')


class OrderSerializer(ModelSerializer):
    products = OrderDetailsSerializer(many=True)

    class Meta:
        model = Order
        fields = ('firstname', 'lastname', 'address', 'phonenumber', 'products')
