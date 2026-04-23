def send_message(self, message: str, **kwargs: Any) -> None:
        """Send a message to a Simplepush user."""
        title = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)

        attachments = None
        # event can now be passed in the service data
        event = None
        if data := kwargs.get(ATTR_DATA):
            event = data.get(ATTR_EVENT)

            attachments_data = data.get(ATTR_ATTACHMENTS)
            if isinstance(attachments_data, list):
                attachments = []
                for attachment in attachments_data:
                    if not (
                        isinstance(attachment, dict)
                        and (
                            "image" in attachment
                            or "video" in attachment
                            or ("video" in attachment and "thumbnail" in attachment)
                        )
                    ):
                        _LOGGER.error("Attachment format is incorrect")
                        return

                    if "video" in attachment and "thumbnail" in attachment:
                        attachments.append(attachment)
                    elif "video" in attachment:
                        attachments.append(attachment["video"])
                    elif "image" in attachment:
                        attachments.append(attachment["image"])

        # use event from config until YAML config is removed
        event = event or self._event

        try:
            if self._password:
                send(
                    key=self._device_key,
                    password=self._password,
                    salt=self._salt,
                    title=title,
                    message=message,
                    attachments=attachments,
                    event=event,
                )
            else:
                send(
                    key=self._device_key,
                    title=title,
                    message=message,
                    attachments=attachments,
                    event=event,
                )

        except BadRequest:
            _LOGGER.error("Bad request. Title or message are too long")
        except UnknownError:
            _LOGGER.error("Failed to send the notification")