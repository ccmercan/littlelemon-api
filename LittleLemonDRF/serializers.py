from rest_framework import serializers
from .models import Category,MenuItem
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User

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