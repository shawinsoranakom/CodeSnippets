def has_permission(self, request):
        return request.user.is_active and (
            request.user.is_staff or request.user.has_perm(PERMISSION_NAME)
        )