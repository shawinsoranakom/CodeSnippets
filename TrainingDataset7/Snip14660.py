def npgettext_lazy(context, singular, plural, number=None):
    return lazy_number(
        npgettext, str, context=context, singular=singular, plural=plural, number=number
    )