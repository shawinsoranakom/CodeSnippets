async def async_generic_view(request):
                    if request.method.lower() != method_name:
                        return HttpResponseNotAllowed(method_name)
                    return HttpResponse(status=200)