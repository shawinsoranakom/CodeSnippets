def _get_repr_options(self):
        options = super()._get_repr_options()
        if self.distinct:
            options["distinct"] = self.distinct
        if self.filter:
            options["filter"] = self.filter
        if self.order_by:
            options["order_by"] = self.order_by
        return options