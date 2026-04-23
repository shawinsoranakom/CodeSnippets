def error(request, message, extra_tags="", fail_silently=False):
    """Add a message with the ``ERROR`` level."""
    add_message(
        request,
        constants.ERROR,
        message,
        extra_tags=extra_tags,
        fail_silently=fail_silently,
    )