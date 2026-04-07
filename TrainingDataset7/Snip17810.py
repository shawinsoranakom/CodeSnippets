def create_dummy_user(self):
        """
        Create a user and return a tuple (user_object, username, email).
        """
        username = "jsmith"
        email = "jsmith@example.com"
        user = User.objects.create_user(username, email, "test123")
        return (user, username, email)