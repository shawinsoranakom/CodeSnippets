def _prepare(self):
        """
        Prepare the message for serialization by forcing the ``message``
        and ``extra_tags`` to str in case they are lazy translations.
        """
        self.message = str(self.message)
        self.extra_tags = str(self.extra_tags) if self.extra_tags is not None else None