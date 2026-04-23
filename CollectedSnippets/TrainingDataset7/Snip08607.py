def check_response(self, response, callback, name=None):
        """
        Raise an error if the view returned None or an uncalled coroutine.
        """
        if not (response is None or asyncio.iscoroutine(response)):
            return
        if not name:
            if isinstance(callback, types.FunctionType):  # FBV
                name = "The view %s.%s" % (callback.__module__, callback.__name__)
            else:  # CBV
                name = "The view %s.%s.__call__" % (
                    callback.__module__,
                    callback.__class__.__name__,
                )
        if response is None:
            raise ValueError(
                "%s didn't return an HttpResponse object. It returned None "
                "instead." % name
            )
        elif asyncio.iscoroutine(response):
            raise ValueError(
                "%s didn't return an HttpResponse object. It returned an "
                "unawaited coroutine instead. You may need to add an 'await' "
                "into your view." % name
            )