def info(request, message, extra_tags="", fail_silently=False):
    """Add a message with the ``INFO`` level."""
    add_message(
        request,
        constants.INFO,
        message,
        extra_tags=extra_tags,
        fail_silently=fail_silently,
    )