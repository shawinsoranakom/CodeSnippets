def field(self):
        """
        Makes ReverseManyToOneDescriptor work in both directions.
        """
        return self.remote_field