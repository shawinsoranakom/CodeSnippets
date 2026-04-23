def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.keys == other.keys
            and self.messages == other.messages
            and self.strict == other.strict
        )