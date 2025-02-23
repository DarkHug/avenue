from django import forms
from .models import Apartment, Fixation


class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = ['object', 'room', 'square_m', 'floor', 'max_floor', 'block', 'status', 'completion', 'price',
                  'windows', 'builder', 'quantity']


class FixationForm(forms.ModelForm):
    class Meta:
        model = Fixation
        fields = ['apartment', 'user', 'buyer', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['apartment'].widget = forms.HiddenInput()  # Скрытое поле для квартиры
        self.fields['user'].widget = forms.HiddenInput()  # Скрытое поле для пользователя
        self.fields['status'].widget = forms.HiddenInput()  # Скрытое поле для статуса
