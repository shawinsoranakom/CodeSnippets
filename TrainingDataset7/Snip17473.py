def __enter__(self):
        self._old_au_local_m2m = AbstractUser._meta.local_many_to_many
        self._old_pm_local_m2m = PermissionsMixin._meta.local_many_to_many
        groups = models.ManyToManyField(Group, blank=True)
        groups.contribute_to_class(PermissionsMixin, "groups")
        user_permissions = models.ManyToManyField(Permission, blank=True)
        user_permissions.contribute_to_class(PermissionsMixin, "user_permissions")
        PermissionsMixin._meta.local_many_to_many = [groups, user_permissions]
        AbstractUser._meta.local_many_to_many = [groups, user_permissions]