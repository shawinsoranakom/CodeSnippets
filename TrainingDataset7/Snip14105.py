def url_patterns(self):
        # urlconf_module might be a valid set of patterns, so we default to it
        patterns = getattr(self.urlconf_module, "urlpatterns", self.urlconf_module)
        try:
            iter(patterns)
        except TypeError as e:
            msg = (
                "The included URLconf '{name}' does not appear to have "
                "any patterns in it. If you see the 'urlpatterns' variable "
                "with valid patterns in the file then the issue is probably "
                "caused by a circular import."
            )
            raise ImproperlyConfigured(msg.format(name=self.urlconf_name)) from e
        return patterns