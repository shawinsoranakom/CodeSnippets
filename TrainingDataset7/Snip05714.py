def get_readonly_fields(self, request, obj=None):
        """
        Hook for specifying custom readonly fields.
        """
        return self.readonly_fields