def _store(self, messages, response, *args, **kwargs):
        """
        Store a list of messages to the request's session.
        """
        if messages:
            self.request.session[self.session_key] = self.serialize_messages(messages)
        else:
            self.request.session.pop(self.session_key, None)
        return []