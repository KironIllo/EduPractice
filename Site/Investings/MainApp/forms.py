from django import forms
from .models import Transaction

class transactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['user', 'moneyid', 'money', 'count', 'price', 'endprice']
        widgets = {
            'user': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'true', 'hidden': 'true'}),
            'moneyid': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'true', 'hidden': 'true'}),
            'money': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'true'}),
            'count': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'true'}),
            'endprice': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'true'})
        }