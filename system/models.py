from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Apartment(models.Model):
    unique_id = models.AutoField(primary_key=True)
    object = models.CharField(verbose_name='Квартира', max_length=255)
    room = models.IntegerField(verbose_name='Комнат')
    square_m = models.FloatField(verbose_name='Площадь')
    floor = models.IntegerField(verbose_name='Этаж')
    max_floor = models.IntegerField(verbose_name='Макс. Этажей')
    block = models.CharField(max_length=50, verbose_name='Пятно')
    status = models.CharField(max_length=50)
    completion = models.DateField(verbose_name='Отделка')
    price = models.DecimalField(max_digits=50, decimal_places=2, verbose_name='Цена')
    windows = models.CharField(max_length=255, verbose_name='Вид')
    builder = models.CharField(max_length=50, verbose_name='Застройщик')
    quantity = models.IntegerField(verbose_name='Кол-во')

    def __str__(self):
        return f"Квартира: {self.object}- Пятно: {self.block} - Комнат: {self.room} - Площадь: {self.square_m}, {self.floor}/{self.max_floor} этаж"


class Buyer(models.Model):
    unique_id = models.AutoField(primary_key=True)
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

    unique_id = models.AutoField(primary_key=True)
    apartment = models.ForeignKey(Apartment, verbose_name='Квартира', on_delete=models.CASCADE,
                                  related_name="fixations")
    user = models.ForeignKey(User, verbose_name='Менеджер', on_delete=models.CASCADE, related_name="fixations")
    buyer = models.ForeignKey(Buyer, verbose_name='Покупатель', on_delete=models.CASCADE, related_name="fixations")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    expires_at = models.DateTimeField(verbose_name='Дата истечения', blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS, default="QUEUE")
    prolong_count = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.expires_at = timezone.now() + timezone.timedelta(days=3)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fixation {self.unique_id}: {self.user.username} -> {self.buyer} -> {self.apartment}"
