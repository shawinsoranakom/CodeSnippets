async def async_browse_media(
        self,
        item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """Return media."""
        if item.identifier:
            config_id, device_id, kind, path = self._parse_identifier(item.identifier)
            config = device = None
            if config_id:
                config = self._get_config_or_raise(config_id)
            if device_id:
                device = self._get_device_or_raise(device_id)
            if kind:
                self._verify_kind_or_raise(kind)
            path = self._get_path_or_raise(path)

            if config and device and kind:
                return await self._build_media_path(config, device, kind, path)
            if config and device:
                return self._build_media_kinds(config, device)
            if config:
                return self._build_media_devices(config)
        return self._build_media_configs()