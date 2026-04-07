def password_change_done(self, request, extra_context=None):
        """
        Display the "success" page after a password change.
        """
        from django.contrib.auth.views import PasswordChangeDoneView

        defaults = {
            "extra_context": {**self.each_context(request), **(extra_context or {})},
        }
        if self.password_change_done_template is not None:
            defaults["template_name"] = self.password_change_done_template
        request.current_app = self.name
        return PasswordChangeDoneView.as_view(**defaults)(request)