def _prepare_messages(self, messages):
        """
        Prepare a list of messages for storage.
        """
        for message in messages:
            message._prepare()