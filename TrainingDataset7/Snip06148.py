def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        usable_password = value and not value.startswith(UNUSABLE_PASSWORD_PREFIX)
        context["button_label"] = (
            _("Reset password") if usable_password else _("Set password")
        )
        return context