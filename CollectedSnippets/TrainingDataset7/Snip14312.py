def E(self):
        """
        Alternative month names as required by some locales. Proprietary
        extension.
        """
        return MONTHS_ALT[self.data.month]