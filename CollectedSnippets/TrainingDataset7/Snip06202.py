def verify(self, password, encoded):
        """Check if the given password is correct."""
        raise NotImplementedError(
            "subclasses of BasePasswordHasher must provide a verify() method"
        )