# urls.py  (app-level)
from django.urls import path
from .views import (
    CategoryView,
    MenuItemListCreateView,
    MenuItemDetailView,
    GroupUsersView,
    GroupUserDeleteView,
    CartMenuItemsView,
    OrdersView,
    OrderDetailView,
)

urlpatterns = [
    # Menu items
    path("menu-items", MenuItemListCreateView.as_view()),
    path("menu-items/<int:pk>", MenuItemDetailView.as_view()),

    # Category
    path("categories", CategoryView.as_view()),

    # Group management
    path("groups/manager/users", GroupUsersView.as_view(), {"group_name": "Manager"}),
    path("groups/manager/users/<int:user_id>", GroupUserDeleteView.as_view(), {"group_name": "Manager"}),
    path("groups/delivery-crew/users", GroupUsersView.as_view(), {"group_name": "Delivery crew"}),
    path("groups/delivery-crew/users/<int:user_id>", GroupUserDeleteView.as_view(), {"group_name": "Delivery crew"}),

    # Cart
    path("cart/menu-items", CartMenuItemsView.as_view()),

    # Orders
    path("orders", OrdersView.as_view()),
    path("orders/<int:order_id>", OrderDetailView.as_view()),
]
