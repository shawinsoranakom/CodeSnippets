async def async_sensitive_method_view_nested(request):
    return await Klass().async_method_nested(request)