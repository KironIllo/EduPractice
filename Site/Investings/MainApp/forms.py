from django import forms
from .models import Transaction

class transactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['money', 'count', 'price']
        widgets = {
            'money': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'true'}),
            'count': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'true'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'true'})
        }