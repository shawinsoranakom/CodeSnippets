def broken_view(request):
    """A view which just raises an exception, simulating a broken view."""
    raise KeyError("Oops! Looks like you wrote some bad code.")