def post(self, path, *args, **kwargs):
        redirect_url = self._get_password_reset_confirm_redirect_url(path)
        return super().post(redirect_url, *args, **kwargs)