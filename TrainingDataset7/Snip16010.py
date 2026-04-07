def get_readonly_fields(self, request, obj=None):
        if obj and obj.published:
            return ("slug",)
        return self.readonly_fields