def add_message(request, level, message, extra_tags="", fail_silently=False):
    """
    Attempt to add a message to the request using the 'messages' app.
    """
    try:
        messages = request._messages
    except AttributeError:
        if not hasattr(request, "META"):
            raise TypeError(
                "add_message() argument must be an HttpRequest object, not "
                "'%s'." % request.__class__.__name__
            )
        if not fail_silently:
            raise MessageFailure(
                "You cannot add messages without installing "
                "django.contrib.messages.middleware.MessageMiddleware"
            )
    else:
        return messages.add(level, message, extra_tags)