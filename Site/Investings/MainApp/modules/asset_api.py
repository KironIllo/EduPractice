from django.http import JsonResponse
from MainApp.modules.prices import get_currency_price
from MainApp.modules.asset import generate_chart_data

def get_current_price(request, ID):
    price_data = get_currency_price(ID)
    if price_data:
        return JsonResponse({'price': float(price_data['rate']), 'change': 0})
    return JsonResponse({'error': 'Not found'}, status=404)

def get_chart_data(request, ID):
    days = int(request.GET.get('days', 30))
    data = generate_chart_data(ID, days)
    return JsonResponse(data)