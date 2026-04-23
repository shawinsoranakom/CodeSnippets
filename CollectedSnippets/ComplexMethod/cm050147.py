def _get_image_by_url(self, url, session):
        maxsize = tools.config.get("import_file_maxbytes")
        _logger.debug("Trying to import image from URL: %s", url)
        try:
            response = session.get(url, timeout=tools.config.get("import_file_timeout"))
            response.raise_for_status()

            if response.headers.get('Content-Length') and int(response.headers['Content-Length']) > maxsize:
                raise ImportValidationError(
                    _("File size exceeds configured maximum (%s bytes)", maxsize)
                )

            content = bytearray()
            for chunk in response.iter_content(DEFAULT_IMAGE_CHUNK_SIZE):
                content += chunk
                if len(content) > maxsize:
                    raise ImportValidationError(
                        _("File size exceeds configured maximum (%s bytes)", maxsize)
                    )

            image = Image.open(io.BytesIO(content))
            w, h = image.size
            if w * h > 42e6:
                raise ImportValidationError(
                    _("Image size excessive, imported images must be smaller than 42 million pixel")
                )

            return content
        except UnidentifiedImageError:
            _logger.warning('This file could not be decoded as an image file.', exc_info=True)
            raise
        except Exception as e:
            _logger.exception(e)
            raise ImportValidationError(_("Could not retrieve URL: %s", url)) from e