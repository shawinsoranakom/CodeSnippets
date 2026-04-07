def get_permission_required(self):
        """
        Override this method to override the permission_required attribute.
        Must return an iterable.
        """
        if self.permission_required is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the "
                f"permission_required attribute. Define "
                f"{self.__class__.__name__}.permission_required, or override "
                f"{self.__class__.__name__}.get_permission_required()."
            )
        if isinstance(self.permission_required, str):
            perms = (self.permission_required,)
        else:
            perms = self.permission_required
        return perms