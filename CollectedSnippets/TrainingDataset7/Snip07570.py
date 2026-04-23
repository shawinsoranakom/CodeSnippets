def get_messages(request):
    """
    Return the message storage on the request if it exists, otherwise return
    an empty list.
    """
    return getattr(request, "_messages", [])