def get_all_permissions(self, obj=None):
        return _user_get_permissions(self, obj, "all")