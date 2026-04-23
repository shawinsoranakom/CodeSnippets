async def stream_source(self) -> str | None:
        """Return the source of the stream."""
        if self._stream_source is None:
            return None

        try:
            stream_url = self._stream_source.async_render(parse_result=False)
            url = yarl.URL(stream_url)
            if (
                not url.user
                and not url.password
                and self._username
                and self._password
                and url.is_absolute()
            ):
                url = url.with_user(self._username).with_password(self._password)
            return str(url)
        except TemplateError as err:
            _LOGGER.error("Error parsing template %s: %s", self._stream_source, err)
            return None