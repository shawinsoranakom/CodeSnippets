def has_change_permission(self, request, obj=None):
        """Only allow changing objects with even id number"""
        return request.user.is_staff and (obj is not None) and (obj.id % 2 == 0)