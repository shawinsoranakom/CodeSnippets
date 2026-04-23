def get_all_permissions(self, user, obj=None):
        if not obj:
            return []  # We only support row level perms

        if not isinstance(obj, TestObj):
            return ["none"]

        if user.is_anonymous:
            return ["anon"]
        if user.username == "test2":
            return ["simple", "advanced"]
        else:
            return ["simple"]