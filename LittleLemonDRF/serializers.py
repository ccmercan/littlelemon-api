from rest_framework import serializers
from .models import Category,MenuItem
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, MenuItem, Cart, Order, OrderItem
class CategorySerializer(serializers.ModelSerializer):
    """user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )"""

    class Meta:
        model = Category
        fields = ['slug', 'title']
        


class MenuItemSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    category = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = MenuItem
        fields = ['title', 'price','featured','category','category_id']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class CartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    menuitem = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())

    class Meta:
        model = Cart
        fields = ["id", "user", "menuitem", "quantity", "unit_price", "price"]
        read_only_fields = ["unit_price", "price"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("quantity must be > 0")
        return value

    def create(self, validated_data):
        menuitem = validated_data["menuitem"]
        qty = validated_data["quantity"]
        validated_data["unit_price"] = menuitem.price
        validated_data["price"] = menuitem.price * qty
        return super().create(validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "menuitem", "quantity", "unit_price", "price"]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    delivery_crew = serializers.StringRelatedField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "delivery_crew", "status", "total", "date", "items"]


class OrderUpdateByManagerSerializer(serializers.ModelSerializer):
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    status = serializers.BooleanField(required=False)

    class Meta:
        model = Order
        fields = ["delivery_crew", "status"]


class OrderUpdateByDeliverySerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(required=True)

    class Meta:
        model = Order
        fields = ["status"]