def load(self):
        s = self._get_session_from_db()
        return self.decode(s.session_data) if s else {}