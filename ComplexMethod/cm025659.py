async def _async_update_data(self) -> BeautifulSoup:
        """Fetch data from Rest."""
        if CONF_RESOURCE_TEMPLATE in self._rest_config:
            self._rest.set_url(
                self._rest_config["resource_template"].async_render(parse_result=False)
            )
        if CONF_PAYLOAD_TEMPLATE in self._rest_config:
            self._rest.set_payload(
                self._rest_config["payload_template"].async_render(parse_result=False)
            )
        await self._rest.async_update()
        if (data := self._rest.data) is None:
            raise UpdateFailed("REST data is not available")

        # Detect if content is XML and use appropriate parser
        # Check Content-Type header first (most reliable), then fall back to content detection
        parser = "lxml"
        headers = self._rest.headers
        content_type = headers.get("Content-Type", "") if headers else ""
        if content_type.startswith(XML_MIME_TYPES):
            parser = "lxml-xml"
        elif isinstance(data, str):
            data_stripped = data.lstrip()
            if data_stripped.startswith("<?xml"):
                # Check if this is HTML5 with XML declaration (XHTML5)
                # by looking for HTML markers after the XML declaration
                xml_end = data_stripped.find("?>")
                if xml_end != -1:
                    after_xml = data_stripped[xml_end + 2 :].lstrip()
                    after_xml_lower = after_xml.lower()
                    is_html = after_xml_lower.startswith(("<!doctype html", "<html"))
                    if is_html:
                        # Strip XML declaration from HTML to avoid XMLParsedAsHTMLWarning
                        data = after_xml
                    else:
                        parser = "lxml-xml"
                else:
                    # Malformed XML declaration, treat as XML
                    parser = "lxml-xml"

        soup = await self.hass.async_add_executor_job(BeautifulSoup, data, parser)
        _LOGGER.debug("Raw beautiful soup: %s", soup)
        return soup