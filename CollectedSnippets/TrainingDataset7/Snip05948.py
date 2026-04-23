def _get_default_ordering(self):
        ordering = []
        if self.model_admin.ordering:
            ordering = self.model_admin.ordering
        elif self.lookup_opts.ordering:
            ordering = self.lookup_opts.ordering
        return ordering