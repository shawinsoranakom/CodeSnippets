async def async_exception_in_render(request):
    class CustomHttpResponse(HttpResponse):
        async def render(self):
            raise Exception("Exception in HttpResponse.render()")

    return CustomHttpResponse("Error")