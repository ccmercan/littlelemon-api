
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    UserSerializer,
    CartSerializer,
    OrderSerializer,
    OrderUpdateByManagerSerializer,
    OrderUpdateByDeliverySerializer,
)


MANAGER_GROUP = "Manager"
DELIVERY_GROUP = "Delivery crew"


def is_manager(user):
    return user.is_authenticated and user.groups.filter(name=MANAGER_GROUP).exists()


def is_delivery(user):
    return user.is_authenticated and user.groups.filter(name=DELIVERY_GROUP).exists()


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return is_manager(request.user)


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (not is_manager(request.user)) and (not is_delivery(request.user))


class MenuItemsPermission(BasePermission):
    # Managers: full access. Others: read-only.
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return request.method in ("GET", "HEAD", "OPTIONS")
        if is_manager(request.user):
            return True
        return request.method in ("GET", "HEAD", "OPTIONS")


class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class MenuItemListCreateView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    permission_classes = [MenuItemsPermission]


class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    permission_classes = [MenuItemsPermission]


class GroupUsersView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get_group(self, group_name):
        group, _ = Group.objects.get_or_create(name=group_name)
        return group

    def get(self, request, group_name):
        group = self.get_group(group_name)
        users = group.user_set.all()
        return Response(UserSerializer(users, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, group_name):
        group = self.get_group(group_name)
        user_id = request.data.get("user_id") or request.data.get("id")
        user = get_object_or_404(User, pk=user_id)
        group.user_set.add(user)
        return Response({"detail": "added"}, status=status.HTTP_201_CREATED)


class GroupUserDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def delete(self, request, group_name, user_id):
        group, _ = Group.objects.get_or_create(name=group_name)
        user = get_object_or_404(User, pk=user_id)
        group.user_set.remove(user)
        return Response({"detail": "removed"}, status=status.HTTP_200_OK)


class CartMenuItemsView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        qs = Cart.objects.filter(user=request.user).select_related("menuitem")
        return Response(CartSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CartSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response({"detail": "deleted"}, status=status.HTTP_200_OK)


class OrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if is_manager(request.user):
            qs = Order.objects.all().prefetch_related("items__menuitem")
        elif is_delivery(request.user):
            qs = Order.objects.filter(delivery_crew=request.user).prefetch_related("items__menuitem")
        else:
            qs = Order.objects.filter(user=request.user).prefetch_related("items__menuitem")
        return Response(OrderSerializer(qs, many=True).data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        if is_manager(request.user) or is_delivery(request.user):
            return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

        cart_items = Cart.objects.filter(user=request.user).select_related("menuitem")
        if not cart_items.exists():
            return Response({"detail": "cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=request.user, total=0)
        total = 0
        for c in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=c.menuitem,
                quantity=c.quantity,
                unit_price=c.unit_price,
                price=c.price,
            )
            total += c.price

        order.total = total
        order.save()
        cart_items.delete()

        order = Order.objects.prefetch_related("items__menuitem").get(pk=order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order.objects.prefetch_related("items__menuitem"), pk=order_id)
        if is_manager(request.user):
            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        if is_delivery(request.user):
            if order.delivery_crew_id != request.user.id:
                return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        if order.user_id != request.user.id:
            return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    def patch(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)

        if is_manager(request.user):
            ser = OrderUpdateByManagerSerializer(order, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(OrderSerializer(Order.objects.prefetch_related("items__menuitem").get(pk=order_id)).data, status=status.HTTP_200_OK)

        if is_delivery(request.user):
            if order.delivery_crew_id != request.user.id:
                return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
            ser = OrderUpdateByDeliverySerializer(order, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(OrderSerializer(Order.objects.prefetch_related("items__menuitem").get(pk=order_id)).data, status=status.HTTP_200_OK)

        return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

    def put(self, request, order_id):
        if not is_manager(request.user):
            return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
        order = get_object_or_404(Order, pk=order_id)
        ser = OrderUpdateByManagerSerializer(order, data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(OrderSerializer(Order.objects.prefetch_related("items__menuitem").get(pk=order_id)).data, status=status.HTTP_200_OK)

    def delete(self, request, order_id):
        if not is_manager(request.user):
            return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
        order = get_object_or_404(Order, pk=order_id)
        order.delete()
        return Response({"detail": "deleted"}, status=status.HTTP_200_OK)
