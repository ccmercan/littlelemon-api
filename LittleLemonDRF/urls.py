from django.urls import path 
from . import views 
  
urlpatterns = [ 
    path('category', views.CategoryView.as_view()), 
    path('menu-item',views.MenuItemView.as_view()),
    path('menu-item/<int:pk>',views.MenuSingleView.as_view()),
] 