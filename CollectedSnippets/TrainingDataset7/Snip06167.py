def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        password = self.fields.get("password")
        if password:
            if self.instance and not self.instance.has_usable_password():
                password.help_text = _(
                    "Enable password-based authentication for this user by setting a "
                    "password."
                )
        user_permissions = self.fields.get("user_permissions")
        if user_permissions:
            user_permissions.queryset = user_permissions.queryset.select_related(
                "content_type"
            )