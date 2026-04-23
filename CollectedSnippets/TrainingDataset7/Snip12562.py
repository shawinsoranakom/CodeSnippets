def add_initial_prefix(self, field_name):
        """Add an 'initial' prefix for checking dynamic initial values."""
        return "initial-%s" % self.add_prefix(field_name)