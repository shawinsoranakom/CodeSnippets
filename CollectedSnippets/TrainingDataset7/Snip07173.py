def import_user_input(self, user_input):
        "Import the Spatial Reference from the given user input string."
        capi.from_user_input(self.ptr, force_bytes(user_input))