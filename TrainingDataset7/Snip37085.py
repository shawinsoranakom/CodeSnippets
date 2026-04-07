async def async_sensitive_view_nested(request):
    try:
        await async_sensitive_function(request)
    except Exception:
        exc_info = sys.exc_info()
        send_log(request, exc_info)
        return technical_500_response(request, *exc_info)