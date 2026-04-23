def view_with_argument(request, name):
    """A view that takes a string argument

    The purpose of this view is to check that if a space is provided in
    the argument, the test framework unescapes the %20 before passing
    the value to the view.
    """
    if name == "Arthur Dent":
        return HttpResponse("Hi, Arthur")
    else:
        return HttpResponse("Howdy, %s" % name)