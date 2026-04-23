def update(self, dict_):
        self._session.update(dict_)
        self.modified = True