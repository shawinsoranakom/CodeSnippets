def return_json_response(request):
    content_type = request.GET.get("content_type")
    kwargs = {"content_type": content_type} if content_type else {}
    return JsonResponse({"key": "value"}, **kwargs)