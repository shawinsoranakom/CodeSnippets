async def async_view(request):
            response = HttpResponse()
            response.content = b"test"
            response["Cache-Control"] = "public"
            return response