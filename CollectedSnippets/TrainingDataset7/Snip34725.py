def authenticate(self, request, username=None, password=None):
        try:
            user = CustomUser.custom_objects.get_by_natural_key(username)
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None