def nesting_exception_view(request):
    """
    A view that uses a nested client to call another view and then raises an
    exception.
    """
    client = Client()
    client.get("/get_view/")
    raise Exception("exception message")