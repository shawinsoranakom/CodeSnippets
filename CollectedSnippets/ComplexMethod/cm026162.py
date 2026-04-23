def send_message(self, message: str, **kwargs: Any) -> None:
        """Send a message to a specified target.

        If no target specified, a 'normal' push will be sent to all devices
        linked to the Pushbullet account.
        Email is special, these are assumed to always exist. We use a special
        call which doesn't require a push object.
        """
        targets: list[str] = kwargs.get(ATTR_TARGET, [])
        title: str = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)
        data: dict[str, Any] = kwargs[ATTR_DATA] or {}

        if not targets:
            # Backward compatibility, notify all devices in own account.
            self._push_data(message, title, data, self.pushbullet)
            _LOGGER.debug("Sent notification to self")
            return

        # refresh device and channel targets
        self.pushbullet.refresh()

        # Main loop, process all targets specified.
        for target in targets:
            try:
                ttype, tname = target.split("/", 1)
            except ValueError as err:
                raise ValueError(f"Invalid target syntax: '{target}'") from err

            # Target is email, send directly, don't use a target object.
            # This also seems to work to send to all devices in own account.
            if ttype == "email":
                self._push_data(message, title, data, self.pushbullet, email=tname)
                _LOGGER.debug("Sent notification to email %s", tname)
                continue

            # Target is sms, send directly, don't use a target object.
            if ttype == "sms":
                self._push_data(
                    message, title, data, self.pushbullet, phonenumber=tname
                )
                _LOGGER.debug("Sent sms notification to %s", tname)
                continue

            if ttype not in self.pbtargets:
                raise ValueError(f"Invalid target syntax: {target}")

            tname = tname.lower()

            if tname not in self.pbtargets[ttype]:
                raise ValueError(f"Target: {target} doesn't exist")

            # Attempt push_note on a dict value. Keys are types & target
            # name. Dict pbtargets has all *actual* targets.
            self._push_data(message, title, data, self.pbtargets[ttype][tname])
            _LOGGER.debug("Sent notification to %s/%s", ttype, tname)