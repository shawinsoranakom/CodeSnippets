def __html__(self):
        """
        Return the html representation of a string for interoperability.

        This allows other template engines to understand Django's SafeData.
        """
        return self