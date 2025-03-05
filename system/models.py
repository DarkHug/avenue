from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

import json


class Debt(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, verbose_name='Менеджер', on_delete=models.CASCADE, related_name="debts")
    debt_sum = models.DecimalField(max_digits=100, decimal_places=0, default=0)
    fix_amount = models.DecimalField(max_digits=100, decimal_places=0, default=0)

    def __str__(self):
        return f"Долг менеджера - {self.user.username}, составляет: {self.debt_sum}тг"


class Apartment(models.Model):
    id = models.AutoField(primary_key=True)
    object = models.CharField(verbose_name='Квартира', max_length=255)
    room = models.IntegerField(verbose_name='Комнат')
    square_m = models.FloatField(verbose_name='Площадь')
    floor = models.IntegerField(verbose_name='Этаж')
    max_floor = models.IntegerField(verbose_name='Макс. Этажей')
    block = models.CharField(max_length=50, verbose_name='Пятно')
    status = models.CharField(max_length=50)
    completion = models.CharField(verbose_name='Сдача')
    price = models.DecimalField(max_digits=50, decimal_places=2, verbose_name='Цена')
    windows = models.CharField(max_length=255, verbose_name='Вид')
    builder = models.CharField(max_length=50, verbose_name='Застройщик')
    quantity = models.IntegerField(verbose_name='Кол-во')

    def __str__(self):
        return f"Квартира: {self.object}- Пятно: {self.block} - Комнат: {self.room} - Площадь: {self.square_m}, {self.floor}/{self.max_floor} этаж"


class Buyer(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='Имя', max_length=255)  # Имя покупателя
    number = models.CharField(verbose_name='Номер', max_length=15)  # Номер телефона покупателя

    def __str__(self):
        return f"Покупатель: {self.name}"


class Fixation(models.Model):
    ACTIVE = "ACTIVE"
    QUEUE = "QUEUE"
    STATUS = (
        (ACTIVE, "АКТИВНЫЙ"),
        (QUEUE, "В ОЧЕРЕДИ"),
    )

    id = models.AutoField(primary_key=True)
    apartment = models.ForeignKey(Apartment, verbose_name='Квартира', on_delete=models.CASCADE,
                                  related_name="fixations")
    user = models.ForeignKey(User, verbose_name='Менеджер', on_delete=models.CASCADE, related_name="fixations")
    buyer = models.ForeignKey(Buyer, verbose_name='Покупатель', on_delete=models.CASCADE, related_name="fixations")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    expires_at = models.DateTimeField(verbose_name='Дата истечения', blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS, default="QUEUE")
    prolong_count = models.IntegerField(default=0)
    cooling_period_end = models.DateTimeField(verbose_name='Конец периода блокировки', blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        if is_new:
            self.expires_at = timezone.now() + timezone.timedelta(days=3)
        super().save(*args, **kwargs)

        # Create history object if it doesn't exist
        history, created = FixationHistory.objects.get_or_create(fixation=self)

        # Add event to history
        action_type = 'create' if is_new else 'update'
        details = {
            'status': self.status,
            'user': self.user.username,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'prolong_count': self.prolong_count
        }

        history.add_event(action_type, details)

    def delete(self, *args, **kwargs):
        # Get the history before deletion
        try:
            history = self.history

            # Add a deletion event with apartment and buyer information
            details = {
                'status': self.status,
                'user': self.user.username,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'prolong_count': self.prolong_count,
                'deleted_at': timezone.now().isoformat(),
                # Add these fields to preserve apartment and buyer information
                'apartment': str(self.apartment),
                'apartment_id': self.apartment.id,
                'buyer': str(self.buyer),
                'buyer_id': self.buyer.id,
                'buyer_name': self.buyer.name,
                'buyer_number': self.buyer.number
            }
            history.add_event('delete', details)
        except FixationHistory.DoesNotExist:
            pass  # No history to update

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Fixation {self.id}: {self.user.username} -> {self.buyer} -> {self.apartment}"


class FixationHistory(models.Model):
    fixation = models.OneToOneField(Fixation, on_delete=models.SET_NULL, related_name='history', null=True, blank=True)
    history_data = models.JSONField(default=list)

    # Add a field to store fixation ID for reference after deletion
    fixation_id_reference = models.IntegerField(null=True, blank=True)

    def add_event(self, action_type, details=None):
        event = {
            'timestamp': timezone.now().isoformat(),
            'action': action_type,
            'details': details or {}
        }

        # Get current history, append new event, and save
        current_history = self.history_data
        current_history.append(event)
        self.history_data = current_history
        self.save()

        # Keep the fixation ID for reference in case fixation is deleted
        if self.fixation_id and not self.fixation_id_reference:
            self.fixation_id_reference = self.fixation.id
            self.save(update_fields=['fixation_id_reference'])

    def get_latest_event(self):
        """Возвращает последнее событие из истории"""
        if self.history_data and len(self.history_data) > 0:
            return sorted(self.history_data, key=lambda x: x['timestamp'], reverse=True)[0]
        return None


class CoolingPeriod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cooling_periods')
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='cooling_periods')
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'apartment')

    def __str__(self):
        return f"Cooling period for {self.user.username} on {self.apartment} until {self.end_date}"
