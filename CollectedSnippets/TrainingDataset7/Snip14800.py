def _check_request(request, decorator_name):
    # Ensure argument looks like a request.
    if not hasattr(request, "META"):
        raise TypeError(
            f"{decorator_name} didn't receive an HttpRequest. If you are "
            "decorating a classmethod, be sure to use @method_decorator."
        )