def send_message(self, message: str, **kwargs: Any) -> None:
        """Send a message to an Android TV device."""
        if self.notify is None:
            try:
                self.notify = Notifications(self.host)
            except ConnectError as err:
                raise HomeAssistantError(
                    f"Failed to connect to host: {self.host}"
                ) from err

        data: dict | None = kwargs.get(ATTR_DATA)
        title = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)
        duration = None
        fontsize = None
        position = None
        transparency = None
        bkgcolor = None
        interrupt = False
        icon = None
        image_file = None
        if data:
            if ATTR_DURATION in data:
                try:
                    duration = int(
                        data.get(ATTR_DURATION, Notifications.DEFAULT_DURATION)
                    )
                except ValueError:
                    _LOGGER.warning(
                        "Invalid duration-value: %s", data.get(ATTR_DURATION)
                    )
            if ATTR_FONTSIZE in data:
                if data.get(ATTR_FONTSIZE) in Notifications.FONTSIZES:
                    fontsize = data.get(ATTR_FONTSIZE)
                else:
                    _LOGGER.warning(
                        "Invalid fontsize-value: %s", data.get(ATTR_FONTSIZE)
                    )
            if ATTR_POSITION in data:
                if data.get(ATTR_POSITION) in Notifications.POSITIONS:
                    position = data.get(ATTR_POSITION)
                else:
                    _LOGGER.warning(
                        "Invalid position-value: %s", data.get(ATTR_POSITION)
                    )
            if ATTR_TRANSPARENCY in data:
                if data.get(ATTR_TRANSPARENCY) in Notifications.TRANSPARENCIES:
                    transparency = data.get(ATTR_TRANSPARENCY)
                else:
                    _LOGGER.warning(
                        "Invalid transparency-value: %s",
                        data.get(ATTR_TRANSPARENCY),
                    )
            if ATTR_COLOR in data:
                if data.get(ATTR_COLOR) in Notifications.BKG_COLORS:
                    bkgcolor = data.get(ATTR_COLOR)
                else:
                    _LOGGER.warning("Invalid color-value: %s", data.get(ATTR_COLOR))
            if ATTR_INTERRUPT in data:
                try:
                    interrupt = cv.boolean(data.get(ATTR_INTERRUPT))
                except vol.Invalid:
                    _LOGGER.warning(
                        "Invalid interrupt-value: %s", data.get(ATTR_INTERRUPT)
                    )
            if imagedata := data.get(ATTR_IMAGE):
                if isinstance(imagedata, str):
                    image_file = (
                        self.load_file(url=imagedata)
                        if imagedata.startswith("http")
                        else self.load_file(local_path=imagedata)
                    )
                elif isinstance(imagedata, dict):
                    image_file = self.load_file(
                        url=imagedata.get(ATTR_IMAGE_URL),
                        local_path=imagedata.get(ATTR_IMAGE_PATH),
                        username=imagedata.get(ATTR_IMAGE_USERNAME),
                        password=imagedata.get(ATTR_IMAGE_PASSWORD),
                        auth=imagedata.get(ATTR_IMAGE_AUTH),
                    )
                else:
                    raise ServiceValidationError(
                        "Invalid image provided",
                        translation_domain=DOMAIN,
                        translation_key="invalid_notification_image",
                        translation_placeholders={"type": type(imagedata).__name__},
                    )
            if icondata := data.get(ATTR_ICON):
                if isinstance(icondata, str):
                    icondata = (
                        self.load_file(url=icondata)
                        if icondata.startswith("http")
                        else self.load_file(local_path=icondata)
                    )
                elif isinstance(icondata, dict):
                    icon = self.load_file(
                        url=icondata.get(ATTR_ICON_URL),
                        local_path=icondata.get(ATTR_ICON_PATH),
                        username=icondata.get(ATTR_ICON_USERNAME),
                        password=icondata.get(ATTR_ICON_PASSWORD),
                        auth=icondata.get(ATTR_ICON_AUTH),
                    )
                else:
                    raise ServiceValidationError(
                        "Invalid Icon provided",
                        translation_domain=DOMAIN,
                        translation_key="invalid_notification_icon",
                        translation_placeholders={"type": type(icondata).__name__},
                    )

        try:
            self.notify.send(
                message,
                title=title,
                duration=duration,
                fontsize=fontsize,
                position=position,
                bkgcolor=bkgcolor,
                transparency=transparency,
                interrupt=interrupt,
                icon=icon,
                image_file=image_file,
            )
        except ConnectError as err:
            raise HomeAssistantError(f"Failed to connect to host: {self.host}") from err