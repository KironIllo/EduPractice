from django.db import models
from django.conf import settings
from django.core import validators
from django.contrib.auth.forms import UserCreationForm


class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    moneyid = models.CharField(max_length=100)
    money = models.CharField(max_length=200)
    count = models.FloatField(max_length=100, validators=[validators.MinValueValidator(0.1)], default=1)
    price = models.FloatField(max_length=100)
    endprice = models.FloatField(max_length=100)

class userB(UserCreationForm):
    balance = models.FloatField(max_length=100)