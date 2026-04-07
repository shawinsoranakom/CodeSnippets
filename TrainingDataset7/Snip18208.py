def clean_username(self, username):
        """
        Grabs username before the @ character.
        """
        return username.split("@")[0]