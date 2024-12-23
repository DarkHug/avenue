from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('apartment/new/', views.apartment_new, name='apartment_new'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
]
