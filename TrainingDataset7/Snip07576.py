def warning(request, message, extra_tags="", fail_silently=False):
    """Add a message with the ``WARNING`` level."""
    add_message(
        request,
        constants.WARNING,
        message,
        extra_tags=extra_tags,
        fail_silently=fail_silently,
    )