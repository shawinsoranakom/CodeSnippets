def mocked_connect(self):
            if self.settings_dict["NAME"] is None:
                raise DatabaseError()
            return orig_connect(self)