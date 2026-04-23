def inner(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        response.headers["X-Robots-Tag"] = "noindex, noodp, noarchive"
        return response