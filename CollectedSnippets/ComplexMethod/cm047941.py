def _import_file_by_url(self, url, session, field, line_number):
        """ Imports a file by URL

        :param str url: the original field value
        :param requests.Session session:
        :param str field: name of the field (for logging/debugging)
        :param int line_number: 0-indexed line number within the imported file (for logging/debugging)
        :return: the replacement value
        :rtype: bytes
        """
        assert re.match(config.get("import_url_regex"), url)
        maxsize = config.get("import_file_maxbytes")
        _logger.debug("Trying to import file from URL: %s into field %s, at line %s", url, field, line_number)
        try:
            response = session.get(url, timeout=config.get("import_file_timeout"))
            response.raise_for_status()

            if response.headers.get('Content-Length') and int(response.headers['Content-Length']) > maxsize:
                raise ImportValidationError(
                    _("File size exceeds configured maximum (%s bytes)", maxsize),
                    field=field
                )

            content = bytearray()
            for chunk in response.iter_content(DEFAULT_CHUNK_SIZE):
                content += chunk
                if len(content) > maxsize:
                    raise ImportValidationError(
                        _("File size exceeds configured maximum (%s bytes)", maxsize),
                        field=field
                    )

            if not guess_mimetype(content).startswith('image/'):
                return base64.b64encode(content)

            image = Image.open(io.BytesIO(content))
            w, h = image.size
            if w * h > 42e6:  # Nokia Lumia 1020 photo resolution
                raise ImportValidationError(
                    _("Image size excessive, imported images must be smaller than 42 million pixel"),
                    field=field
                )

            return base64.b64encode(content)
        except Exception as e:
            _logger.warning(e, exc_info=True)
            raise ImportValidationError(_("Could not retrieve URL: %(url)s [%(field_name)s: L%(line_number)d]: %(error)s") % {
                'url': url,
                'field_name': field,
                'line_number': line_number + 1,
                'error': e
            })