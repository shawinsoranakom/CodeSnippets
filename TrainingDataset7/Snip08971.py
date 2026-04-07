def start_object(self, obj):
        """
        Called when serializing of an object starts.
        """
        raise NotImplementedError(
            "subclasses of Serializer must provide a start_object() method"
        )