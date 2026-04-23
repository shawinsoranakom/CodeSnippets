def get_template(self, template_name, skip=None):
        """
        Perform the caching that gives this loader its name. Often many of the
        templates attempted will be missing, so memory use is of concern here.
        To keep it in check, caching behavior is a little complicated when a
        template is not found. See ticket #26306 for more details.

        With template debugging disabled, cache the TemplateDoesNotExist class
        for every missing template and raise a new instance of it after
        fetching it from the cache.

        With template debugging enabled, a unique TemplateDoesNotExist object
        is cached for each missing template to preserve debug data. When
        raising an exception, Python sets __traceback__, __context__, and
        __cause__ attributes on it. Those attributes can contain references to
        all sorts of objects up the call chain and caching them creates a
        memory leak. Thus, unraised copies of the exceptions are cached and
        copies of those copies are raised after they're fetched from the cache.
        """
        key = self.cache_key(template_name, skip)
        cached = self.get_template_cache.get(key)
        if cached:
            if isinstance(cached, type) and issubclass(cached, TemplateDoesNotExist):
                raise cached(template_name)
            elif isinstance(cached, TemplateDoesNotExist):
                raise copy_exception(cached)
            return cached

        try:
            template = super().get_template(template_name, skip)
        except TemplateDoesNotExist as e:
            self.get_template_cache[key] = (
                copy_exception(e) if self.engine.debug else TemplateDoesNotExist
            )
            raise
        else:
            self.get_template_cache[key] = template

        return template