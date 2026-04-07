def add(self, level, message, extra_tags=""):
        """
        Queue a message to be stored.

        The message is only queued if it contained something and its level is
        not less than the recording level (``self.level``).
        """
        if not message:
            return
        # Check that the message level is not less than the recording level.
        level = int(level)
        if level < self.level:
            return
        # Add the message.
        self.added_new = True
        message = Message(level, message, extra_tags=extra_tags)
        self._queued_messages.append(message)