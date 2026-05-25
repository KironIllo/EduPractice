from django.db import models
from django.conf import settings
from django.core import validators
from django.contrib.auth.models import User

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('buy', 'Покупка'),
        ('sell', 'Продажа'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    moneyid = models.CharField(max_length=100)
    money = models.CharField(max_length=200)
    count = models.DecimalField(max_digits=10, decimal_places=2, validators=[validators.MinValueValidator(0.01)], default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    endprice = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)