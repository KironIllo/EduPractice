from django.http import JsonResponse
from MainApp.modules.asset_utils import get_asset_price
from MainApp.modules.asset import generate_chart_data
from MainApp.modules.metals_api import get_metal_price_history

def get_current_price(request, ID):
    asset = get_asset_price(ID)
    if asset:
        return JsonResponse({'price': float(asset['price']), 'change': 0})
    return JsonResponse({'error': 'Not found'}, status=404)

def get_chart_data(request, ID):
    days = int(request.GET.get('days', 30))
    if str(ID).isdigit():
        data = get_metal_price_history(int(ID), days=days)
    else:
        data = generate_chart_data(ID, days)
    return JsonResponse(data)