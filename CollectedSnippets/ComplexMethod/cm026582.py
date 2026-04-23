async def async_send_message(self, message: str, **kwargs: Any) -> None:
        """Login to Discord, send message to channel(s) and log out."""
        nextcord.VoiceClient.warn_nacl = False
        discord_bot = nextcord.Client()
        images = []
        embedding = None

        if ATTR_TARGET not in kwargs:
            _LOGGER.error("No target specified")
            return

        data = kwargs.get(ATTR_DATA) or {}

        embeds: list[nextcord.Embed] = []
        if ATTR_EMBED in data:
            embedding = data[ATTR_EMBED]
            title = embedding.get(ATTR_EMBED_TITLE)
            description = embedding.get(ATTR_EMBED_DESCRIPTION)
            color = embedding.get(ATTR_EMBED_COLOR)
            url = embedding.get(ATTR_EMBED_URL)
            fields = embedding.get(ATTR_EMBED_FIELDS) or []

            if embedding:
                embed = nextcord.Embed(
                    title=title, description=description, color=color, url=url
                )
                for field in fields:
                    embed.add_field(**field)
                if ATTR_EMBED_FOOTER in embedding:
                    embed.set_footer(**embedding[ATTR_EMBED_FOOTER])
                if ATTR_EMBED_AUTHOR in embedding:
                    embed.set_author(**embedding[ATTR_EMBED_AUTHOR])
                if ATTR_EMBED_THUMBNAIL in embedding:
                    embed.set_thumbnail(**embedding[ATTR_EMBED_THUMBNAIL])
                if ATTR_EMBED_IMAGE in embedding:
                    embed.set_image(**embedding[ATTR_EMBED_IMAGE])
                embeds.append(embed)

        if ATTR_IMAGES in data:
            for image in data.get(ATTR_IMAGES, []):
                image_exists = await self.hass.async_add_executor_job(
                    self.file_exists, image
                )

                filename = os.path.basename(image)

                if image_exists:
                    images.append((image, filename))

        if ATTR_URLS in data:
            for url in data.get(ATTR_URLS, []):
                file = await self.async_get_file_from_url(
                    url,
                    data.get(ATTR_VERIFY_SSL, True),
                    MAX_ALLOWED_DOWNLOAD_SIZE_BYTES,
                )

                if file is not None:
                    filename = os.path.basename(url)

                    images.append((BytesIO(file), filename))

        await discord_bot.login(self.token)

        try:
            for channelid in kwargs[ATTR_TARGET]:
                channelid = int(channelid)
                # Must create new instances of File for each channel.
                files = [nextcord.File(image, filename) for image, filename in images]
                try:
                    channel = cast(
                        Messageable, await discord_bot.fetch_channel(channelid)
                    )
                except nextcord.NotFound:
                    try:
                        channel = await discord_bot.fetch_user(channelid)
                    except nextcord.NotFound:
                        _LOGGER.warning("Channel not found for ID: %s", channelid)
                        continue
                await channel.send(message, files=files, embeds=embeds)
        except (nextcord.HTTPException, nextcord.NotFound) as error:
            _LOGGER.warning("Communication error: %s", error)
        await discord_bot.close()