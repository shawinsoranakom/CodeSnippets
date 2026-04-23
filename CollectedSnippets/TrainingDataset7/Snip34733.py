def load(self):
        try:
            return self.decode(self.session_key)
        except Exception:
            self.modified = True
            return {}