from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('apartment/new/', views.apartment_new, name='apartment_new'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path("logout/", views.logout_handler, name="logout"),
    path('fixation/<int:apartment_id>/', views.create_fixation, name='create_fixation'),
    path('fixation_form/<int:apartment_id>/', views.fixation_form, name='fixation_form'),
    path('apartment/<int:apartment_id>/fixations/', views.apartment_fixations, name='apartment_fixations'),
    path('my_fixations/', views.my_fixations, name='my_fixations'),
    path('delete_fixation/<int:fixation_id>', views.delete_fixation, name='delete_fixation'),
    path('prolong/<int:fixation_id>', views.prolong_fixations, name='prolong_fixation'),
]
