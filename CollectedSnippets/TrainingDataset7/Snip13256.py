def debug(request):
    """
    Return context variables helpful for debugging.
    """
    context_extras = {}
    if settings.DEBUG and request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS:
        context_extras["debug"] = True
        from django.db import connections

        # Return a lazy reference that computes connection.queries on access,
        # to ensure it contains queries triggered after this function runs.
        context_extras["sql_queries"] = lazy(
            lambda: list(
                itertools.chain.from_iterable(
                    connections[x].queries for x in connections
                )
            ),
            list,
        )
    return context_extras