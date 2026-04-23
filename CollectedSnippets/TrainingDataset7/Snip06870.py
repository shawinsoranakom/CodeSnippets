def has_changed(self, initial, data):
        """Compare geographic value of data with its initial value."""

        try:
            data = self.to_python(data)
            initial = self.to_python(initial)
        except ValidationError:
            return True

        # Only do a geographic comparison if both values are available
        if initial and data:
            data.transform(initial.srid)
            # If the initial value was not added by the browser, the geometry
            # provided may be slightly different, the first time it is saved.
            # The comparison is done with a very low tolerance.
            return not initial.equals_exact(data, tolerance=0.000001)
        else:
            # Check for change of state of existence
            return bool(initial) != bool(data)