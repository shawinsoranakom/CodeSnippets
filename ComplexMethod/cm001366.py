async def display_message(
        self,
        message: str,
        level: MessageLevel = MessageLevel.INFO,
        title: str | None = None,
        preserve_color: bool = False,
    ) -> None:
        """Display a general message.

        Args:
            message: The message content.
            level: The message severity level.
            title: Optional title/prefix for the message.
            preserve_color: Whether to preserve ANSI color codes.
        """
        extra: dict[str, Any] = {}
        if title:
            extra["title"] = title
        if preserve_color:
            extra["preserve_color"] = True

        if level == MessageLevel.DEBUG:
            self.logger.debug(message, extra=extra if extra else None)
        elif level == MessageLevel.INFO:
            self.logger.info(message, extra=extra if extra else None)
        elif level == MessageLevel.WARNING:
            self.logger.warning(message, extra=extra if extra else None)
        elif level == MessageLevel.ERROR:
            self.logger.error(message, extra=extra if extra else None)
        elif level == MessageLevel.SUCCESS:
            extra["color"] = Fore.GREEN
            self.logger.info(message, extra=extra)