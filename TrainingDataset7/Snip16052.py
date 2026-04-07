def has_change_permission(self, request, obj=None):
        # Simulate that the user can't change a specific object.
        return obj is None