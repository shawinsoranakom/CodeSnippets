def get_readonly_fields(self, request, obj=None):
        if obj and obj.published:
            return ("subslug",)
        return self.readonly_fields