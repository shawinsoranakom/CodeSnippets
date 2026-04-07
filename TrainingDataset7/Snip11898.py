def _property_names(self):
        """Return a set of the names of the properties defined on the model."""
        names = set()
        seen = set()
        for klass in self.model.__mro__:
            names |= {
                name
                for name, value in klass.__dict__.items()
                if isinstance(value, property) and name not in seen
            }
            seen |= set(klass.__dict__)
        return frozenset(names)