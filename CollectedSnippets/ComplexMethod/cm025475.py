async def post(self, request: web.Request) -> web.Response:
        """Handle upload."""
        hass = request.app[http.KEY_HASS]

        # Increase max payload
        request._client_max_size = MAX_UPLOAD_SIZE  # noqa: SLF001

        try:
            data = self.schema(dict(await request.post()))
        except vol.Invalid as err:
            LOGGER.error("Received invalid upload data: %s", err)
            raise web.HTTPBadRequest from err

        try:
            target_folder = MediaSourceItem.from_uri(
                hass, data["media_content_id"], None
            )
        except ValueError as err:
            LOGGER.error("Received invalid upload data: %s", err)
            raise web.HTTPBadRequest from err

        if target_folder.domain != DOMAIN:
            raise web.HTTPBadRequest

        source = cast(LocalSource, hass.data[MEDIA_SOURCE_DATA][target_folder.domain])
        try:
            uploaded_media_source_id = await source.async_upload_media(
                target_folder, data["file"]
            )
        except Unresolvable as err:
            LOGGER.error("Invalid local source ID: %s", data["media_content_id"])
            raise web.HTTPBadRequest from err
        except InvalidFileNameError as err:
            LOGGER.error("Invalid filename uploaded: %s", data["file"].filename)
            raise web.HTTPBadRequest from err
        except PathNotSupportedError as err:
            LOGGER.error("Invalid path for upload: %s", data["media_content_id"])
            raise web.HTTPBadRequest from err
        except OSError as err:
            LOGGER.error("Error uploading file: %s", err)
            raise web.HTTPInternalServerError from err

        return self.json({"media_content_id": uploaded_media_source_id})