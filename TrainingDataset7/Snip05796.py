def get_extra(self, request, obj=None, **kwargs):
        """Hook for customizing the number of extra inline forms."""
        return self.extra