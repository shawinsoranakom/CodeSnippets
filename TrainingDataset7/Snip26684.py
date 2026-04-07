def same_origin_response(request):
            response = HttpResponse()
            response.sameorigin = True
            return response