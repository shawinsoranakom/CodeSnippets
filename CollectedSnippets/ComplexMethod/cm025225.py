def send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to specified target."""
        targets: list[str] | None
        if (targets := kwargs.get(ATTR_TARGET)) is None:
            targets = ["a"]
            _LOGGER.debug("No target specified. Sending push to all")
        else:
            _LOGGER.debug("%s target(s) specified", len(targets))

        title = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)
        data = kwargs.get(ATTR_DATA) or {}

        # Converting the specified image to base64
        picture1 = data.get(ATTR_PICTURE1)
        picture1_encoded = ""
        if picture1 is not None:
            _LOGGER.debug("picture1 is available")
            url = picture1.get(ATTR_PICTURE1_URL, None)
            local_path = picture1.get(ATTR_PICTURE1_PATH, None)
            username = picture1.get(ATTR_PICTURE1_USERNAME)
            password = picture1.get(ATTR_PICTURE1_PASSWORD)
            auth = picture1.get(ATTR_PICTURE1_AUTH)

            if url is not None:
                _LOGGER.debug("Loading image from url %s", url)
                picture1_encoded = self.load_from_url(url, username, password, auth)
            elif local_path is not None:
                _LOGGER.debug("Loading image from file %s", local_path)
                picture1_encoded = self.load_from_file(local_path)
            else:
                _LOGGER.warning("Missing url or local_path for picture1")
        else:
            _LOGGER.debug("picture1 is not specified")

        payload = {
            "k": self._private_key,
            "t": title,
            "m": message,
            "s": data.get(ATTR_SOUND, ""),
            "v": data.get(ATTR_VIBRATION, ""),
            "i": data.get(ATTR_ICON, ""),
            "c": data.get(ATTR_ICONCOLOR, ""),
            "u": data.get(ATTR_URL, ""),
            "ut": data.get(ATTR_URLTITLE, ""),
            "l": data.get(ATTR_TIME2LIVE, ""),
            "pr": data.get(ATTR_PRIORITY, ""),
            "re": data.get(ATTR_RETRY, ""),
            "ex": data.get(ATTR_EXPIRE, ""),
            "cr": data.get(ATTR_CONFIRM, ""),
            "a": data.get(ATTR_ANSWER, ""),
            "ao": data.get(ATTR_ANSWEROPTIONS, ""),
            "af": data.get(ATTR_ANSWERFORCE, ""),
            "p": picture1_encoded,
        }

        for target in targets:
            payload["d"] = target
            response = requests.post(_RESOURCE, data=payload, timeout=CONF_TIMEOUT)
            if response.status_code != HTTPStatus.OK:
                _LOGGER.error("Pushsafer failed with: %s", response.text)
            else:
                _LOGGER.debug("Push send: %s", response.json())