def inner(request):
            try:
                response = get_response(request)
            except Exception as exc:
                response = response_for_exception(request, exc)
            return response