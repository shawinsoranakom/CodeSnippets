def _store(self, messages, response, *args, **kwargs):
        """
        Store a list of messages and return a list of any messages which could
        not be stored.

        One type of object must be able to be stored, ``Message``.

        **This method must be implemented by a subclass.**
        """
        raise NotImplementedError(
            "subclasses of BaseStorage must provide a _store() method"
        )