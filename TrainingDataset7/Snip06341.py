def has_perm(self, perm, obj=None):
        return _user_has_perm(self, perm, obj=obj)