def send(self, fail_silently=False):
        """Send the email message."""
        if not self.recipients():
            # Don't bother creating the network connection if there's nobody to
            # send to.
            return 0

        if fail_silently and self.connection:
            raise TypeError(
                "fail_silently cannot be used with a connection. "
                "Pass fail_silently to get_connection() instead."
            )

        return self.get_connection(fail_silently).send_messages([self])