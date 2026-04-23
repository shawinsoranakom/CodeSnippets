def force_login(self, user, backend=None):
        if backend is None:
            backend = self._get_backend()
        user.backend = backend
        self._login(user, backend)