def handle_m2m_field(self, obj, field):
        """
        Called to handle a ManyToManyField.
        """
        raise NotImplementedError(
            "subclasses of Serializer must provide a handle_m2m_field() method"
        )