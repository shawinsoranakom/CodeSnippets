def print_message(  # pylint: disable=locally-disabled, invalid-name
        self,
        message: str,
        color: t.Optional[str] = None,
        stderr: bool = False,
        truncate: bool = False,
    ) -> None:
        """Display a message."""
        if self.redact and self.sensitive:
            for item in self.sensitive:
                if not item:
                    continue

                message = message.replace(item, '*' * len(item))

        if truncate:
            if len(message) > self.truncate > 5:
                message = message[:self.truncate - 5] + ' ...'

        if color and self.color:
            # convert color resets in message to desired color
            message = message.replace(self.clear, color)
            message = '%s%s%s' % (color, message, self.clear)

        fd = sys.stderr if stderr else self.fd

        print(message, file=fd)
        fd.flush()