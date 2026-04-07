def get_prepopulated_fields(self, request, obj=None):
        if obj and obj.published:
            return {}
        return self.prepopulated_fields