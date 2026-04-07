def identifier_converter(self, name):
        """Identifier comparison is case insensitive under Oracle."""
        return name.lower()