def keep_query(*keep_params, **additional_params):
    """
    Generate a query string keeping the current request querystring's parameters specified
    in ``keep_params`` and also adds the parameters specified in ``additional_params``.

    Multiple values query string params will be merged into a single one with comma seperated
    values.

    The ``keep_params`` arguments can use wildcards too, eg:

        keep_query('search', 'shop_*', page=4)
    """
    if not keep_params and not additional_params:
        keep_params = ('*',)
    params = additional_params.copy()
    qs_keys = list(request.httprequest.args) if request else []
    for keep_param in keep_params:
        for param in fnmatch.filter(qs_keys, keep_param):
            if param not in additional_params and param in qs_keys:
                params[param] = request.httprequest.args.getlist(param)
    return werkzeug.urls.url_encode(params)