from django import forms
from .models import Apartment


class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = ['object', 'room', 'square_m', 'floor', 'max_floor', 'block', 'status', 'completion', 'price',
                  'windows', 'builder', 'quantity']
