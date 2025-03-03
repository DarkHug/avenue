from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import ApartmentForm
from .models import Apartment, Fixation, Buyer


# ---------------------Login Section---------------------

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


# ---------------------Apartment Section---------------------


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


def all_apartments(request):
    apartments = Apartment.objects.all()
    return render(request, 'all_apartments.html', context={'apartments': apartments})


def apartment_edit(request, pk):
    apartment = get_object_or_404(Apartment, pk=pk)

    if request.method == "POST":
        form = ApartmentForm(request.POST, instance=apartment)
        if form.is_valid():
            apartment = form.save()
            messages.success(request, f"Объект '{apartment.object}' успешно обновлен")
            return redirect('all_apartment')
    else:
        form = ApartmentForm(instance=apartment)

    return render(request, 'apartment_edit.html', {'form': form, 'apartment': apartment})


def apartment_delete(request, pk):
    apartment = get_object_or_404(Apartment, pk=pk)
    apartment.delete()
    return redirect('all_apartment')


# ---------------------Fixation Section---------------------
@login_required
def fixation_form(request, apartment_id):
    # Получаем квартиру по ID
    apartment = get_object_or_404(Apartment, pk=apartment_id)
    return render(request, 'fixation_form.html', {'apartment': apartment})


@login_required
def create_fixation(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)

    # Проверка на количество фиксаций пользователя
    fixation_count = Fixation.objects.filter(apartment=apartment, user=request.user).count()
    print(fixation_count)
    if fixation_count >= 2:
        messages.error(request, f'У вас уже максимум фиксаций')
        return redirect('home')

    if request.method == 'POST':
        buyer_name = request.POST.get('buyer_name')
        buyer_number = request.POST.get('buyer_number')

        # Проверяем, существует ли такой покупатель
        existing_buyer = Buyer.objects.filter(number=buyer_number).first()

        # Если покупатель существует, проверяем, есть ли уже фиксация с этим покупателем на данную квартиру
        if existing_buyer:
            existing_fixation = Fixation.objects.filter(apartment=apartment, buyer=existing_buyer).exists()
            if existing_fixation:
                messages.error(request, f'Этот покупатель уже зафиксирован на данную квартиру')
                return redirect('home')

        buyer, created = Buyer.objects.get_or_create(
            name=buyer_name,
            number=buyer_number,
        )

        status = "ACTIVE"

        active_fixations_count = apartment.fixations.filter(status="ACTIVE").count()

        if active_fixations_count >= 3:
            status = "QUEUE"

        fixation = Fixation.objects.create(
            apartment=apartment,
            user=request.user,
            buyer=buyer,
            status=status,
        )

        return redirect('home')

    return render(request, 'fixation_form.html', {'apartment': apartment})


@login_required
def apartment_fixations(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
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
        return redirect('all_fixations')
    fixation.expires_at += timezone.timedelta(days=3)
    fixation.prolong_count += 1
    fixation.save()
    return redirect('all_fixations')


@login_required
def all_fixations(request):
    fixations = Fixation.objects.all().order_by('user__username')  # Сортировка по имени менеджера
    return render(request, 'all_fixations.html', {'fixations': fixations})
