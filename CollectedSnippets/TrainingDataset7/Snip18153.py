def with_perm(
        self, perm, is_active=True, include_superusers=True, backend=None, obj=None
    ):
        if obj is not None and obj.username == "charliebrown":
            return User.objects.filter(pk=obj.pk)
        return User.objects.filter(username__startswith="charlie")