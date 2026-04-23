def _get(self, *args, **kwargs):
        """
        Retrieve a list of messages from the request's session. This storage
        always stores everything it is given, so return True for the
        all_retrieved flag.
        """
        return (
            self.deserialize_messages(self.request.session.get(self.session_key)),
            True,
        )