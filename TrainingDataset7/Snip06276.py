def get_login_url(self):
        """
        Override this method to override the login_url attribute.
        """
        login_url = self.login_url or settings.LOGIN_URL
        if not login_url:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the login_url attribute. Define "
                f"{self.__class__.__name__}.login_url, settings.LOGIN_URL, or override "
                f"{self.__class__.__name__}.get_login_url()."
            )
        return str(login_url)