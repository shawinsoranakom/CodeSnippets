def _getargspec(object):
    try:
        signature = inspect.signature(object, annotation_format=Format.STRING)
        if signature:
            name = getattr(object, '__name__', '')
            # <lambda> function are always single-line and should not be formatted
            max_width = (80 - len(name)) if name != '<lambda>' else None
            return signature.format(max_width=max_width, quote_annotation_strings=False)
    except (ValueError, TypeError):
        argspec = getattr(object, '__text_signature__', None)
        if argspec:
            if argspec[:2] == '($':
                argspec = '(' + argspec[2:]
            if getattr(object, '__self__', None) is not None:
                # Strip the bound argument.
                m = re.match(r'\(\w+(?:(?=\))|,\s*(?:/(?:(?=\))|,\s*))?)', argspec)
                if m:
                    argspec = '(' + argspec[m.end():]
        return argspec
    return None