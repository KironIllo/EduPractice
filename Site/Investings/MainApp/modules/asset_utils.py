from decimal import Decimal
from MainApp.modules.prices import get_currency_price
from MainApp.modules.metals_api import get_metal_price

def get_asset_price(asset_id):
    """
    Универсальное получение цены актива (валюты или металла)
    Возвращает: {
        'id': str, 'name': str, 'price': Decimal, 'nominal': int,
        'char_code': str, 'unit': str ('шт' или 'г')
    }
    """
    asset_id = str(asset_id)
    # Металлы: ID состоит из одной цифры 1-4
    if asset_id.isdigit() and int(asset_id) in (1, 2, 3, 4):
        metal = get_metal_price(int(asset_id))
        if metal:
            return {
                'id': asset_id,
                'name': metal['name'],
                'price': metal['price'],
                'nominal': metal['nominal'],
                'char_code': metal['char_code'],
                'unit': 'г'
            }
    # Валюты: ID начинается с R
    elif asset_id.startswith('R'):
        currency = get_currency_price(asset_id)
        if currency:
            return {
                'id': currency['id'],
                'name': currency['name'],
                'price': Decimal(currency['rate']),
                'nominal': currency['nominal'],
                'char_code': currency['char_code'],
                'unit': 'шт'
            }
    return None