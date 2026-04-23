def has_perm(self, user, perm, obj=None):
        if not obj:
            return  # We only support row level perms

        if isinstance(obj, TestObj):
            if user.username == "test2":
                return True
            elif user.is_anonymous and perm == "anon":
                return True
            elif not user.is_active and perm == "inactive":
                return True
        return False