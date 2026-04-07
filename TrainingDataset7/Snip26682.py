def xframe_exempt_response(request):
            response = HttpResponse()
            response.xframe_options_exempt = True
            return response