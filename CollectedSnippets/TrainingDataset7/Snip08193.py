def get_context_data(self, **kwargs):
        """
        Return a dictionary to use as extra context if either
        ``self.description_template`` or ``self.item_template`` are used.

        Default implementation preserves the old behavior
        of using {'obj': item, 'site': current_site} as the context.
        """
        return {"obj": kwargs.get("item"), "site": kwargs.get("site")}