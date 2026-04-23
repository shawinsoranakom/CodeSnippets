async def async_sensitive_method_view(request):
    return await Klass().async_method(request)