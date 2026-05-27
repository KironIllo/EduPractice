from django.http import JsonResponse
from MainApp.modules.asset_utils import get_asset_price
from MainApp.modules.asset import generate_chart_data

def get_current_price(request, ID):
    asset = get_asset_price(ID)
    if asset:
        return JsonResponse({'price': float(asset['price']), 'change': 0})
    return JsonResponse({'error': 'Not found'}, status=404)

def get_chart_data(request, ID):
    days = int(request.GET.get('days', 30))
    # Для металлов пока нет графика
    if str(ID).isdigit():
        return JsonResponse({'dates': [], 'prices': []})
    data = generate_chart_data(ID, days)
    return JsonResponse(data)