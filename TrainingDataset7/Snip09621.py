def is_usable(self):
        try:
            self.connection.ping()
        except Database.Error:
            return False
        else:
            return True