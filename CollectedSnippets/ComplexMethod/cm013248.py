def assertGreaterAlmostEqual(self, first, second, places=None, msg=None, delta=None):
        """Assert that ``first`` is greater than or almost equal to ``second``.

        The equality of ``first`` and ``second`` is determined in a similar way to
        the ``assertAlmostEqual`` function of the standard library.
        """
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")

        if first >= second:
            return

        diff = second - first
        if delta is not None:
            if diff <= delta:
                return

            standardMsg = f"{first} not greater than or equal to {second} within {delta} delta"
        else:
            if places is None:
                places = 7

            if round(diff, places) == 0:
                return

            standardMsg = f"{first} not greater than or equal to {second} within {places} places"

        msg = self._formatMessage(msg, standardMsg)
        raise self.failureException(msg)