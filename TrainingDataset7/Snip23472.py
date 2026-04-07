def get_fieldsets(self, request, obj=None):
                return [(None, {"fields": ["url", "description"]})]