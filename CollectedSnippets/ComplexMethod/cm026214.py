def prepare_message(self, message, data) -> Message:
        """Prepare a message to send."""
        msg = Message(message)

        if ATTR_TITLE in data:
            msg.set_title(data[ATTR_TITLE])

        if ATTR_LEVEL in data:
            try:
                msg.set_level(data[ATTR_LEVEL])
            except ValueError as error:
                _LOGGER.warning("Setting level error: %s", error)

        if ATTR_PRIORITY in data:
            try:
                msg.set_priority(data[ATTR_PRIORITY])
            except ValueError as error:
                _LOGGER.warning("Setting priority error: %s", error)

        if ATTR_IMAGES in data:
            for image in data[ATTR_IMAGES]:
                self.attach_file(msg, image, ATTR_FILE_KIND_IMAGE)

        if ATTR_FILES in data:
            for file in data[ATTR_FILES]:
                self.attach_file(msg, file)

        return msg