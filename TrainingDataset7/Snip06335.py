def get_user_permissions(self, obj=None):
        return _user_get_permissions(self, obj, "user")