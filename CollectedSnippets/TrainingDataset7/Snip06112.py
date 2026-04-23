def set_unusable_password(self):
        # Set a value that will never be a valid hash
        self.password = make_password(None)