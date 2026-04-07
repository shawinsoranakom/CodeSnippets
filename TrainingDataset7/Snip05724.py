def has_view_or_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj) or self.has_change_permission(
            request, obj
        )