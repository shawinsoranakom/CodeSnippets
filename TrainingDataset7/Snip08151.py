def get_handler(self, *args, **options):
        """
        Return the static files serving handler wrapping the default handler,
        if static files should be served. Otherwise return the default handler.
        """
        handler = super().get_handler(*args, **options)
        use_static_handler = options["use_static_handler"]
        insecure_serving = options["insecure_serving"]
        if use_static_handler and (settings.DEBUG or insecure_serving):
            return StaticFilesHandler(handler)
        return handler