async def _async_generate_root(self) -> BrowseMediaSource:
        """Return all available reolink cameras as root browsing structure."""
        children: list[BrowseMediaSource] = []

        entity_reg = er.async_get(self.hass)
        device_reg = dr.async_get(self.hass)
        for config_entry in self.hass.config_entries.async_loaded_entries(DOMAIN):
            channels: list[str] = []
            host = config_entry.runtime_data.host
            entities = er.async_entries_for_config_entry(
                entity_reg, config_entry.entry_id
            )
            for entity in entities:
                if (
                    entity.disabled
                    or entity.device_id is None
                    or entity.domain != CAM_DOMAIN
                ):
                    continue

                device = device_reg.async_get(entity.device_id)
                ch_id = entity.unique_id.split("_")[1]
                if ch_id in channels or device is None:
                    continue
                channels.append(ch_id)

                ch: int | str = ch_id
                if len(ch_id) > 3:
                    ch = host.api.channel_for_uid(ch_id)

                if not host.api.supported(int(ch), "replay") or not host.api.hdd_info:
                    # playback stream not supported by this camera or no storage installed
                    continue

                device_name = device.name
                if device.name_by_user is not None:
                    device_name = device.name_by_user

                if host.api.model in DUAL_LENS_MODELS:
                    device_name = f"{device_name} lens {ch}"

                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=f"CAM|{config_entry.entry_id}|{ch}",
                        media_class=MediaClass.CHANNEL,
                        media_content_type=MediaType.PLAYLIST,
                        title=device_name,
                        thumbnail=f"/api/camera_proxy/{entity.entity_id}",
                        can_play=False,
                        can_expand=True,
                    )
                )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.APP,
            media_content_type="",
            title="Reolink",
            can_play=False,
            can_expand=True,
            children=children,
        )