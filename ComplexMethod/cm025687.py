async def get(
        self,
        request: web.Request,
        entity_id: str,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> web.Response:
        """Start a get request."""
        if (player := self.component.get_entity(entity_id)) is None:
            status = (
                HTTPStatus.NOT_FOUND
                if request[KEY_AUTHENTICATED]
                else HTTPStatus.UNAUTHORIZED
            )
            return web.Response(status=status)

        assert isinstance(player, MediaPlayerEntity)
        authenticated = (
            request[KEY_AUTHENTICATED]
            or request.query.get("token") == player.access_token
        )

        if not authenticated:
            return web.Response(status=HTTPStatus.UNAUTHORIZED)

        if media_content_type and media_content_id:
            media_image_id = request.query.get("media_image_id")
            data, content_type = await player.async_get_browse_image(
                media_content_type, media_content_id, media_image_id
            )
        else:
            data, content_type = await player.async_get_media_image()

        if data is None:
            return web.Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

        headers: LooseHeaders = {CACHE_CONTROL: "max-age=3600"}
        return web.Response(body=data, content_type=content_type, headers=headers)