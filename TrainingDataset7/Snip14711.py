def pgettext(context, message):
    msg_with_ctxt = "%s%s%s" % (context, CONTEXT_SEPARATOR, message)
    result = gettext(msg_with_ctxt)
    if CONTEXT_SEPARATOR in result:
        # Translation not found
        result = message
    elif isinstance(message, SafeData):
        result = mark_safe(result)
    return result