def has_view_permission(self, request, obj=None):
        """Only allow viewing objects if id is a multiple of 3."""
        return request.user.is_staff and obj is not None and obj.id % 3 == 0