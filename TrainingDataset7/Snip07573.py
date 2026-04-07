def debug(request, message, extra_tags="", fail_silently=False):
    """Add a message with the ``DEBUG`` level."""
    add_message(
        request,
        constants.DEBUG,
        message,
        extra_tags=extra_tags,
        fail_silently=fail_silently,
    )