def get_prepopulated_fields(self, request, obj=None):
        """
        Hook for specifying custom prepopulated fields.
        """
        return self.prepopulated_fields