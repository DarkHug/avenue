from django.conf import settings
from django.db import models
from django.utils import timezone


class Apartment(models.Model):
    unique_id = models.AutoField(primary_key=True)
    object = models.CharField(max_length=255)
    room = models.IntegerField()
    square_m = models.FloatField()
    floor = models.IntegerField()
    max_floor = models.IntegerField()
    block = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    completion = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    windows = models.CharField()
    builder = models.CharField(max_length=50)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.object} - {self.unique_id}"


class User(models.Model):
    unique_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=15)
    status = models.CharField(max_length=50)
    role = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Buyer(models.Model):
    unique_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Fixation(models.Model):
    unique_id = models.AutoField(primary_key=True)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name="fixations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fixations")
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name="fixations")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Pending")

    def __str__(self):
        return f"Fixation {self.unique_id}: {self.user} -> {self.buyer} -> {self.apartment}"
