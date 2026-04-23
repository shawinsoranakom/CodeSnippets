def exception_in_render(request):
    class CustomHttpResponse(HttpResponse):
        def render(self):
            raise Exception("Exception in HttpResponse.render()")

    return CustomHttpResponse("Error")