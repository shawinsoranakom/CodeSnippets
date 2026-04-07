def has_output(self):
        """
        Return True if some choices would be output for this filter.
        """
        raise NotImplementedError(
            "subclasses of ListFilter must provide a has_output() method"
        )