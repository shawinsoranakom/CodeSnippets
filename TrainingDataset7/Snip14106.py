def resolve_error_handler(self, view_type):
        callback = getattr(self.urlconf_module, "handler%s" % view_type, None)
        if not callback:
            # No handler specified in file; use lazy import, since
            # django.conf.urls imports this file.
            from django.conf import urls

            callback = getattr(urls, "handler%s" % view_type)
        return get_callable(callback)