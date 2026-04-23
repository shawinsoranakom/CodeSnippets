def messages(request):
    """
    Return a lazy 'messages' context variable as well as
    'DEFAULT_MESSAGE_LEVELS'.
    """
    return {
        "messages": get_messages(request),
        "DEFAULT_MESSAGE_LEVELS": DEFAULT_LEVELS,
    }