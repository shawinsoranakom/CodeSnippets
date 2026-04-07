def can_filter(self):
        """
        Return True if adding filters to this instance is still possible.

        Typically, this means no limits or offsets have been put on the
        results.
        """
        return not self.is_sliced