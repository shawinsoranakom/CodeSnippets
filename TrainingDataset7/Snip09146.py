def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and set(self.allowed_extensions or [])
            == set(other.allowed_extensions or [])
            and self.message == other.message
            and self.code == other.code
        )