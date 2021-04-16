from rest_framework.serializers import ModelSerializer

from foodcartapp.models import Order, OrderDetails, Place


class OrderDetailsSerializer(ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = ('product', 'quantity')


class OrderSerializer(ModelSerializer):
    products = OrderDetailsSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ('firstname', 'lastname', 'address', 'phonenumber', 'products')


class PlaceSerializer(ModelSerializer):
    class Meta:
        model = Place
        fields = "__all__"
