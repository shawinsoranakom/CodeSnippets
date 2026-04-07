def npgettext(context, singular, plural, number):
    msgs_with_ctxt = (
        "%s%s%s" % (context, CONTEXT_SEPARATOR, singular),
        "%s%s%s" % (context, CONTEXT_SEPARATOR, plural),
        number,
    )
    result = ngettext(*msgs_with_ctxt)
    if CONTEXT_SEPARATOR in result:
        # Translation not found
        result = ngettext(singular, plural, number)
    return result