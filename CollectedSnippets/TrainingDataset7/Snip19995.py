def _get_post(self):
        if self.post_error is not None:
            raise self.post_error
        return self._post