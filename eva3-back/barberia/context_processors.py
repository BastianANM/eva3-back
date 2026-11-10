from .services import SESSION_KEY


def reservation_summary(request):
    items = request.session.get(SESSION_KEY, {})
    return {"reserva_count": sum(int(item.get("cantidad", 1)) for item in items.values())}