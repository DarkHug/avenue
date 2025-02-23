from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import ApartmentForm
from .models import Apartment, Fixation, Buyer


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_handler(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    fixation_count = Fixation.objects.filter(user=request.user).count()
    print(fixation_count)
    apartments = Apartment.objects.annotate(fixation_count=Count('fixations'))
    return render(request, 'home.html', {'apartments': apartments})


def apartment_new(request):
    if request.method == 'POST':
        form = ApartmentForm(request.POST)
        if form.is_valid():
            apartment = form.save(commit=False)
            apartment.save()
            return redirect('home')
    else:
        form = ApartmentForm()
    return render(request, 'new_apartment.html', {'form': form})


@login_required
def fixation_form(request, apartment_id):
    # Получаем квартиру по ID
    apartment = get_object_or_404(Apartment, pk=apartment_id)
    return render(request, 'fixation_form.html', {'apartment': apartment})


@login_required
def create_fixation(request, apartment_id):
    apartment = get_object_or_404(Apartment, pk=apartment_id)
    fixation_count = Fixation.objects.filter(apartment=apartment, user=request.user).count()
    print(fixation_count)
    if fixation_count >= 2:
        messages.error(request,
                       f'У вас уже максимум фиксаций')
        return redirect('home')

    if request.method == 'POST':
        buyer_name = request.POST.get('buyer_name')
        buyer_number = request.POST.get('buyer_number')

        buyer, created = Buyer.objects.get_or_create(
            name=buyer_name,
            number=buyer_number,
        )

        fixation = Fixation.objects.create(
            apartment=apartment,
            user=request.user,
            buyer=buyer,
            status="Pending",
        )

        return redirect('home')

    return render(request, 'fixation_form.html', {'apartment': apartment})


@login_required
def apartment_fixations(request, apartment_id):
    apartment = get_object_or_404(Apartment, pk=apartment_id)
    fixations = Fixation.objects.filter(apartment=apartment)
    return render(request, 'apartment_fixations.html', context={'fixations': fixations, 'apartment': apartment})


@login_required
def my_fixations(request):
    fixations = Fixation.objects.filter(user=request.user)
    return render(request, 'my_fixations.html', context={'fixations': fixations})


@login_required
def delete_fixation(request, fixation_id):
    fixation = get_object_or_404(Fixation, pk=fixation_id)
    fixation.delete()
    return redirect('my_fixations')


@login_required
def prolong_fixations(request, fixation_id):
    fixation = get_object_or_404(Fixation, pk=fixation_id)
    if fixation.prolong_count >= 1:
        messages.error(request, f'Уже продлевали, нельзя больше')
        return redirect('my_fixations')
    fixation.expires_at += timezone.timedelta(days=3)
    fixation.prolong_count += 1
    fixation.save()
    return redirect('my_fixations')
