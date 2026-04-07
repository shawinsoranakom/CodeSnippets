def check_custom_error_handlers(app_configs, **kwargs):
    if not getattr(settings, "ROOT_URLCONF", None):
        return []

    from django.urls import get_resolver

    resolver = get_resolver()

    errors = []
    # All handlers take (request, exception) arguments except handler500
    # which takes (request).
    for status_code, num_parameters in [(400, 2), (403, 2), (404, 2), (500, 1)]:
        try:
            handler = resolver.resolve_error_handler(status_code)
        except (ImportError, ViewDoesNotExist) as e:
            path = getattr(resolver.urlconf_module, "handler%s" % status_code)
            msg = (
                "The custom handler{status_code} view '{path}' could not be "
                "imported."
            ).format(status_code=status_code, path=path)
            errors.append(Error(msg, hint=str(e), id="urls.E008"))
            continue
        args = [None] * num_parameters
        try:
            signature(handler).bind(*args)
        except TypeError:
            msg = (
                "The custom handler{status_code} view '{path}' does not "
                "take the correct number of arguments ({args})."
            ).format(
                status_code=status_code,
                path=handler.__module__ + "." + handler.__qualname__,
                args="request, exception" if num_parameters == 2 else "request",
            )
            errors.append(Error(msg, id="urls.E007"))
    return errors