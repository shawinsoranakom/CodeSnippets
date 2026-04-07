def __bool__(self):
        """
        Return True since all formsets have a management form which is not
        included in the length.
        """
        return True