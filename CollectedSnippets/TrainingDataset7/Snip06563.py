def get_distance(self, f, value, lookup_type):
        """
        Return the distance parameters for the given geometry field,
        lookup value, and lookup type.
        """
        raise NotImplementedError(
            "Distance operations not available on this spatial backend."
        )