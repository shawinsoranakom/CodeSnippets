def handle_field(self, obj, field):
        """
        Called to handle each individual (non-relational) field on an object.
        """
        raise NotImplementedError(
            "subclasses of Serializer must provide a handle_field() method"
        )