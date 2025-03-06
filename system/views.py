from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import Count, F
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import ApartmentForm
from .models import Apartment, Fixation, FixationHistory, Buyer, Debt, CoolingPeriod


# ---------------------Login & Profile Section---------------------

@login_required
def user_debt(request):
    debt_sum = Debt.objects.all()

    if debt_sum is None:
        debt_sum = 0

    return render(request, 'user_debt.html', context={'debt_sum': debt_sum})


@login_required
def delete_all_debt(request):
    debt_sum = Debt.objects.all()
    debt_sum.delete()
    return redirect('user_debt')


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

    # Проверка на период охлаждения
    cooling_period = CoolingPeriod.objects.filter(
        user=request.user,
        apartment=apartment,
        end_date__gt=timezone.now()
    ).first()

    if cooling_period:
        days_left = (cooling_period.end_date - timezone.now()).days + 1
        messages.error(request,
                       f"Вы не можете зафиксировать эту квартиру еще {days_left} дней из-за периода охлаждения.")
        return redirect('home')

    if request.method == 'POST':
        buyer_name = request.POST.get('buyer_name')
        buyer_number = request.POST.get('buyer_number')

        # Нормализуем номер телефона для единообразия формата
        # Убедимся, что номер начинается с +7 и имеет правильный формат
        if not buyer_number.startswith('+7'):
            buyer_number = '+7' + buyer_number.lstrip('+').lstrip('7')

        # Очищаем номер от всех символов кроме цифр и '+'
        clean_number = ''.join(c for c in buyer_number if c.isdigit() or c == '+')

        # Убеждаемся, что номер начинается с +7
        if clean_number.startswith('7'):
            clean_number = '+' + clean_number
        elif not clean_number.startswith('+'):
            clean_number = '+7' + clean_number
        elif not clean_number.startswith('+7'):
            clean_number = '+7' + clean_number[1:]

        buyer_number = clean_number

        # Проверяем, существует ли такой покупатель с нормализованным номером
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

        if active_fixations_count >= 5:
            status = "QUEUE"

        fixation = Fixation.objects.create(
            apartment=apartment,
            user=request.user,
            buyer=buyer,
            status=status,
        )

        # Создаем запись истории для новой фиксации
        history, created = FixationHistory.objects.get_or_create(fixation=fixation)
        details = {
            'status': fixation.status,
            'user': request.user.username,
            'expires_at': fixation.expires_at.isoformat() if fixation.expires_at else None,
            'prolong_count': fixation.prolong_count,
            'apartment': str(apartment),
            'buyer': buyer.name,
            'buyer_number': buyer.number
        }
        history.add_event('create', details)

        # Обновляем долг менеджера
        debt, created = Debt.objects.get_or_create(user=request.user, defaults={'debt_sum': 0, 'fix_amount': 0})
        current_fix_amount = Debt.objects.filter(id=debt.id).values_list('fix_amount', flat=True).first()

        if current_fix_amount is not None and current_fix_amount > 5:
            Debt.objects.filter(id=debt.id).update(debt_sum=F('debt_sum') + 5000)

        Debt.objects.filter(id=debt.id).update(fix_amount=F('fix_amount') + 1)

        messages.success(request, f'Фиксация успешно создана')
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

    # Проверка, может ли пользователь продлить эту фиксацию
    if request.user != fixation.user and not request.user.is_staff:
        messages.error(request, 'У вас нет прав для продления этой фиксации')
        return redirect('all_fixations')

    # Проверка на количество продлений
    if fixation.prolong_count >= 1:
        messages.error(request, 'Уже продлевали, нельзя больше')
        return redirect('all_fixations')

    # Проверка, активна ли фиксация
    if fixation.status != "ACTIVE":
        messages.error(request, 'Можно продлевать только активные фиксации')
        return redirect('all_fixations')

    # Продлеваем фиксацию
    fixation.expires_at += timezone.timedelta(days=3)
    fixation.prolong_count += 1

    # Устанавливаем период охлаждения (10 дней после истечения)
    fixation.cooling_period_end = fixation.expires_at + timezone.timedelta(days=10)

    # Сохраняем изменения в фиксации
    fixation.save()

    # Создаем или обновляем запись периода охлаждения
    CoolingPeriod.objects.update_or_create(
        user=fixation.user,
        apartment=fixation.apartment,
        defaults={'end_date': fixation.cooling_period_end}
    )

    # Добавляем событие в историю
    history, created = FixationHistory.objects.get_or_create(fixation=fixation)
    details = {
        'status': fixation.status,
        'user': request.user.username,
        'expires_at': fixation.expires_at.isoformat(),
        'prolong_count': fixation.prolong_count,
        'cooling_period_end': fixation.cooling_period_end.isoformat()
    }
    history.add_event('prolong', details)

    messages.success(request, f'Фиксация успешно продлена до {fixation.expires_at.strftime("%d.%m.%Y")}')
    return redirect('all_fixations')


@login_required
def all_fixations(request):
    fixations = Fixation.objects.all().order_by('user__username')  # Сортировка по имени менеджера
    return render(request, 'all_fixations.html', {'fixations': fixations})


@login_required
def get_fixation_log(request):
    fixations = FixationHistory.objects.all()
    return render(request, 'fixation_history.html', {'fixations': fixations})
