def _push_data(
        self,
        message: str,
        title: str,
        data: dict[str, Any],
        pusher: PushBullet,
        email: str | None = None,
        phonenumber: str | None = None,
    ) -> None:
        """Create the message content."""
        kwargs = {"body": message, "title": title}
        if email:
            kwargs["email"] = email

        try:
            if phonenumber and pusher.devices:
                pusher.push_sms(pusher.devices[0], phonenumber, message)
                return
            if url := data.get(ATTR_URL):
                pusher.push_link(url=url, **kwargs)
                return
            if filepath := data.get(ATTR_FILE):
                if not self.hass.config.is_allowed_path(filepath):
                    raise ValueError("Filepath is not valid or allowed")
                with open(filepath, "rb") as fileh:
                    filedata = self.pushbullet.upload_file(fileh, filepath)
                if filedata.get("file_type") == "application/x-empty":
                    raise ValueError("Cannot send an empty file")
                kwargs.update(filedata)
                pusher.push_file(**kwargs)
            elif (file_url := data.get(ATTR_FILE_URL)) and vol.Url(file_url):
                pusher.push_file(
                    file_name=file_url,
                    file_url=file_url,
                    file_type=(mimetypes.guess_type(file_url)[0]),
                    **kwargs,
                )
            else:
                pusher.push_note(**kwargs)
        except PushError as err:
            raise HomeAssistantError(f"Notify failed: {err}") from err