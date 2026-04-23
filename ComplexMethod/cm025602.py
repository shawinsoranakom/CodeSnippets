async def _async_get_file_image_response(self, file):
        # not all MPD implementations and versions support the `albumart` and
        # `fetchpicture` commands.
        commands = []
        with suppress(mpd.ConnectionError):
            commands = list(await self._client.commands())
        can_albumart = "albumart" in commands
        can_readpicture = "readpicture" in commands

        response = None

        # read artwork embedded into the media file
        if can_readpicture:
            try:
                with suppress(mpd.ConnectionError):
                    response = await self._client.readpicture(file)
            except mpd.CommandError as error:
                if error.errno is not mpd.FailureResponseCode.NO_EXIST:
                    LOGGER.warning(
                        "Retrieving artwork through `readpicture` command failed: %s",
                        error,
                    )

        # read artwork contained in the media directory (cover.{jpg,png,tiff,bmp}) if none is embedded
        if can_albumart and not response:
            try:
                with suppress(mpd.ConnectionError):
                    response = await self._client.albumart(file)
            except mpd.CommandError as error:
                if error.errno is not mpd.FailureResponseCode.NO_EXIST:
                    LOGGER.warning(
                        "Retrieving artwork through `albumart` command failed: %s",
                        error,
                    )

        # response can be an empty object if there is no image
        if not response:
            return None

        return response