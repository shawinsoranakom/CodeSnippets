def xframe_not_exempt_response(request):
            response = HttpResponse()
            response.xframe_options_exempt = False
            return response