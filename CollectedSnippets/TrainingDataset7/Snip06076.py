def _get_user_permissions(self, user_obj):
        return user_obj.user_permissions.all()