async def _async_generate_camera_files(
        self,
        config_entry_id: str,
        channel: int,
        stream: str,
        year: int,
        month: int,
        day: int,
        event: str | None = None,
    ) -> BrowseMediaSource:
        """Return all recording files on a specific day of a Reolink camera."""
        host = get_host(self.hass, config_entry_id)

        start = dt.datetime(year, month, day, hour=0, minute=0, second=0)
        end = dt.datetime(year, month, day, hour=23, minute=59, second=59)

        children: list[BrowseMediaSource] = []
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "Requesting VODs of %s on %s/%s/%s",
                host.api.camera_name(channel),
                year,
                month,
                day,
            )
        event_trigger = VOD_trigger[event] if event is not None else None
        _, vod_files = await host.api.request_vod_files(
            channel,
            start,
            end,
            stream=stream,
            split_time=VOD_SPLIT_TIME,
            trigger=event_trigger,
        )

        if event is None and host.api.is_nvr and not host.api.is_hub:
            triggers = VOD_trigger.NONE
            for file in vod_files:
                triggers |= file.triggers

            children.extend(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"EVE|{config_entry_id}|{channel}|{stream}|{year}|{month}|{day}|{trigger.name}",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaType.PLAYLIST,
                    title=str(trigger.name).title(),
                    can_play=False,
                    can_expand=True,
                )
                for trigger in triggers
            )

        for file in vod_files:
            file_name = f"{file.start_time.time()} {file.duration}"
            if file.triggers != file.triggers.NONE:
                file_name += " " + " ".join(
                    str(trigger.name).title() for trigger in file.triggers
                )

            children.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"FILE|{config_entry_id}|{channel}|{stream}|{file.file_name}|{file.start_time_id}|{file.end_time_id}",
                    media_class=MediaClass.VIDEO,
                    media_content_type=MediaType.VIDEO,
                    title=file_name,
                    can_play=True,
                    can_expand=False,
                )
            )

        title = (
            f"{host.api.camera_name(channel)} {res_name(stream)} {year}/{month}/{day}"
        )
        if host.api.model in DUAL_LENS_MODELS:
            title = f"{host.api.camera_name(channel)} lens {channel} {res_name(stream)} {year}/{month}/{day}"
        if event:
            title = f"{title} {event.title()}"

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"FILES|{config_entry_id}|{channel}|{stream}",
            media_class=MediaClass.CHANNEL,
            media_content_type=MediaType.PLAYLIST,
            title=title,
            can_play=False,
            can_expand=True,
            children=children,
        )