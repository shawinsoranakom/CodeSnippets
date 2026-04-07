def success(request, message, extra_tags="", fail_silently=False):
    """Add a message with the ``SUCCESS`` level."""
    add_message(
        request,
        constants.SUCCESS,
        message,
        extra_tags=extra_tags,
        fail_silently=fail_silently,
    )