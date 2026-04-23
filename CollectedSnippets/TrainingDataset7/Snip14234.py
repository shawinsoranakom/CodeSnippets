def close_all(self):
        for conn in self.all(initialized_only=True):
            conn.close()