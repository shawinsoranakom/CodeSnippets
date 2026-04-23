def hello_with_delay(request):
    name = request.GET.get("name") or "World"
    time.sleep(1)
    return HttpResponse(f"Hello {name}!")