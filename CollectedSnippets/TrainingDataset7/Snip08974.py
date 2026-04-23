def handle_fk_field(self, obj, field):
        """
        Called to handle a ForeignKey field.
        """
        raise NotImplementedError(
            "subclasses of Serializer must provide a handle_fk_field() method"
        )