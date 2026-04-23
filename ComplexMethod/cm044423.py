def format(self, record: logging.LogRecord) -> str:
        """Strip new lines from log records and rewrite certain warning messages to debug level.

        Parameters
        ----------
        record
            The incoming log record to be formatted for entry into the logger.

        Returns
        -------
        The formatted log message
        """
        record = self._lower_external(record)
        record = self._format_warnings(record)
        record.message = record.getMessage()
        # strip newlines
        if record.levelno < 30 and ("\n" in record.message or "\r" in record.message):
            record.message = record.message.replace("\n", "\\n").replace("\r", "\\r")

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        msg = self.formatMessage(record)
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if msg[-1:] != "\n":
                msg = msg + "\n"
            msg = msg + record.exc_text
        if record.stack_info:
            if msg[-1:] != "\n":
                msg = msg + "\n"
            msg = msg + self.formatStack(record.stack_info)
        return msg