def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs["autofocus"] = True
        if self.user.has_usable_password():
            self.fields["password1"].required = False
            self.fields["password2"].required = False
            self.fields["usable_password"] = (
                SetUnusablePasswordMixin.create_usable_password_field(
                    self.usable_password_help_text
                )
            )