def get_for_model(self, model, for_concrete_model=True):
        """
        Return the ContentType object for a given model, creating the
        ContentType if necessary. Lookups are cached so that subsequent lookups
        for the same model don't hit the database.
        """
        opts = self._get_opts(model, for_concrete_model)
        try:
            return self._get_from_cache(opts)
        except KeyError:
            pass

        # The ContentType entry was not found in the cache, therefore we
        # proceed to load or create it.
        try:
            # Start with get() and not get_or_create() in order to use
            # the db_for_read (see #20401).
            ct = self.get(app_label=opts.app_label, model=opts.model_name)
        except self.model.DoesNotExist:
            # Not found in the database; we proceed to create it. This time
            # use get_or_create to take care of any race conditions.
            ct, created = self.get_or_create(
                app_label=opts.app_label,
                model=opts.model_name,
            )
        self._add_to_cache(self.db, ct)
        return ct