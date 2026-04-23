def configure_user(self, request, user, created=True):
        """
        Sets user's email address using the email specified in an HTTP header.
        Sets user's last name for existing users.
        """
        user.email = request.META.get(RemoteUserTest.email_header, "")
        if not created:
            user.last_name = user.username
        user.save()
        return user