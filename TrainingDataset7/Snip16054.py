def confirm_login_allowed(self, user):
        if not user.is_active or not (user.is_staff or user.has_perm(PERMISSION_NAME)):
            raise ValidationError("permission denied")