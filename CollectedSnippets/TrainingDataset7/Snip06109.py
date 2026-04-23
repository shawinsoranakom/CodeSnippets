def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self._password = raw_password