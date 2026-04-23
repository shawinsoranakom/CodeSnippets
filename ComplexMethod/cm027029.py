def get_attachments_as_bytes(
        data: Any,
        attachment_size_limit: int,
        hass: HomeAssistant,
    ) -> list[bytearray] | None:
        """Retrieve attachments from URLs defined in data."""
        try:
            data = DATA_URLS_SCHEMA(data)
        except vol.Invalid:
            return None
        urls = data[ATTR_URLS]

        attachments_as_bytes: list[bytearray] = []

        for url in urls:
            try:
                if not hass.config.is_allowed_external_url(url):
                    _LOGGER.error("URL '%s' not in allow list", url)
                    continue

                resp = requests.get(
                    url, verify=data[ATTR_VERIFY_SSL], timeout=10, stream=True
                )
                resp.raise_for_status()

                if (
                    resp.headers.get("Content-Length") is not None
                    and int(str(resp.headers.get("Content-Length")))
                    > attachment_size_limit
                ):
                    content_length = int(str(resp.headers.get("Content-Length")))
                    raise ValueError(  # noqa: TRY301
                        "Attachment too large (Content-Length reports "
                        f"{content_length}). Max size: "
                        f"{CONF_MAX_ALLOWED_DOWNLOAD_SIZE_BYTES} bytes"
                    )

                size = 0
                chunks = bytearray()
                for chunk in resp.iter_content(1024):
                    size += len(chunk)
                    if size > attachment_size_limit:
                        raise ValueError(  # noqa: TRY301
                            f"Attachment too large (Stream reports {size}). "
                            f"Max size: {CONF_MAX_ALLOWED_DOWNLOAD_SIZE_BYTES} bytes"
                        )

                    chunks.extend(chunk)

                attachments_as_bytes.append(chunks)
            except Exception as ex:
                _LOGGER.error("%s", ex)
                raise

        if not attachments_as_bytes:
            return None

        return attachments_as_bytes