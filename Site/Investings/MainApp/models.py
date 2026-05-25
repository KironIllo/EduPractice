from django.db import models
from django.conf import settings

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    money = models.CharField(max_length=100)
    count = models.FloatField(max_length=100)
    price = models.FloatField(max_length=100)
