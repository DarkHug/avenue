from django.contrib import admin
from .models import Apartment, User, Buyer, Fixation


@admin.register(Fixation)
class FixationAdmin(admin.ModelAdmin):
    list_display = ('user', 'buyer', 'apartment', 'status')


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ('name', 'number')


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('object', 'room', 'square_m', 'floor', 'block', 'price', 'builder')
