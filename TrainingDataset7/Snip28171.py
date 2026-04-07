def assertSequenceEqualWithoutHyphens(self, qs, result):
        """
        Backends with a native datatype for UUID don't support fragment lookups
        without hyphens because they store values with them.
        """
        self.assertSequenceEqual(
            qs,
            [] if connection.features.has_native_uuid_field else result,
        )