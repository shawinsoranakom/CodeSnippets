def T(self):
        """
        Time zone of this machine; e.g. 'EST' or 'MDT'.

        If timezone information is not available, return an empty string.
        """
        if self.timezone is None:
            return ""

        return str(self.timezone.tzname(self.data))