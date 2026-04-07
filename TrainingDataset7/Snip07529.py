def render_to_kml(*args, **kwargs):
    "Render the response as KML (using the correct MIME type)."
    return HttpResponse(
        loader.render_to_string(*args, **kwargs),
        content_type="application/vnd.google-earth.kml+xml",
    )