def get_group_permissions(self, user, obj=None):
        if not obj:
            return  # We only support row level perms

        if not isinstance(obj, TestObj):
            return ["none"]

        if "test_group" in [group.name for group in user.groups.all()]:
            return ["group_perm"]
        else:
            return ["none"]