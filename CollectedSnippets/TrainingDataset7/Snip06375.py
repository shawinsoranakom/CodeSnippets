def _get_secret(self):
        return self._secret or settings.SECRET_KEY