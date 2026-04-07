def check_server_status(self, inner_ex=None):
        """Return True if the server is available."""
        try:
            self.client.query("version")
        except Exception:
            raise WatchmanUnavailable(str(inner_ex)) from inner_ex
        return True