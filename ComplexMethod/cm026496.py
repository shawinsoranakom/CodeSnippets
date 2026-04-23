def get(
        self, request: http.HomeAssistantRequest, briefing_id: str
    ) -> StreamResponse | tuple[bytes, HTTPStatus]:
        """Handle Alexa Flash Briefing request."""
        _LOGGER.debug("Received Alexa flash briefing request for: %s", briefing_id)

        if request.query.get(API_PASSWORD) is None:
            err = "No password provided for Alexa flash briefing: %s"
            _LOGGER.error(err, briefing_id)
            return b"", HTTPStatus.UNAUTHORIZED

        if not hmac.compare_digest(
            request.query[API_PASSWORD].encode("utf-8"),
            self.flash_briefings[CONF_PASSWORD].encode("utf-8"),
        ):
            err = "Wrong password for Alexa flash briefing: %s"
            _LOGGER.error(err, briefing_id)
            return b"", HTTPStatus.UNAUTHORIZED

        if not isinstance(self.flash_briefings.get(briefing_id), list):
            err = "No configured Alexa flash briefing was found for: %s"
            _LOGGER.error(err, briefing_id)
            return b"", HTTPStatus.NOT_FOUND

        briefing = []

        for item in self.flash_briefings.get(briefing_id, []):
            output = {}
            if item.get(CONF_TITLE) is not None:
                if isinstance(item.get(CONF_TITLE), template.Template):
                    output[ATTR_TITLE_TEXT] = item[CONF_TITLE].async_render(
                        parse_result=False
                    )
                else:
                    output[ATTR_TITLE_TEXT] = item.get(CONF_TITLE)

            if item.get(CONF_TEXT) is not None:
                if isinstance(item.get(CONF_TEXT), template.Template):
                    output[ATTR_MAIN_TEXT] = item[CONF_TEXT].async_render(
                        parse_result=False
                    )
                else:
                    output[ATTR_MAIN_TEXT] = item.get(CONF_TEXT)

            if (uid := item.get(CONF_UID)) is None:
                uid = str(uuid.uuid4())
            output[ATTR_UID] = uid

            if item.get(CONF_AUDIO) is not None:
                if isinstance(item.get(CONF_AUDIO), template.Template):
                    output[ATTR_STREAM_URL] = item[CONF_AUDIO].async_render(
                        parse_result=False
                    )
                else:
                    output[ATTR_STREAM_URL] = item.get(CONF_AUDIO)

            if item.get(CONF_DISPLAY_URL) is not None:
                if isinstance(item.get(CONF_DISPLAY_URL), template.Template):
                    output[ATTR_REDIRECTION_URL] = item[CONF_DISPLAY_URL].async_render(
                        parse_result=False
                    )
                else:
                    output[ATTR_REDIRECTION_URL] = item.get(CONF_DISPLAY_URL)

            output[ATTR_UPDATE_DATE] = dt_util.utcnow().strftime(DATE_FORMAT)

            briefing.append(output)

        return self.json(briefing)