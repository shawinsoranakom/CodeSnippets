async def get(
        self, request: web.Request, source_dir_id: str, location: str
    ) -> web.Response:
        """Start a GET request."""
        if not self.hass.config_entries.async_loaded_entries(DOMAIN):
            raise web.HTTPNotFound
        # location: {cache_key}/{filename}
        cache_key, file_name, passphrase = location.split("/")
        image_id = int(cache_key.split("_")[0])

        if shared := file_name.endswith(SHARED_SUFFIX):
            file_name = file_name.removesuffix(SHARED_SUFFIX)

        mime_type, _ = mimetypes.guess_type(file_name)
        if not isinstance(mime_type, str):
            raise web.HTTPNotFound

        entry: SynologyDSMConfigEntry | None = (
            self.hass.config_entries.async_entry_for_domain_unique_id(
                DOMAIN, source_dir_id
            )
        )
        if TYPE_CHECKING:
            assert entry
        diskstation = entry.runtime_data
        if TYPE_CHECKING:
            assert diskstation.api.photos is not None
        item = SynoPhotosItem(image_id, "", "", "", cache_key, "xl", shared, passphrase)
        try:
            if passphrase:
                image = await diskstation.api.photos.download_item_thumbnail(item)
            else:
                image = await diskstation.api.photos.download_item(item)
        except SynologyDSMException as exc:
            raise web.HTTPNotFound from exc
        return web.Response(body=image, content_type=mime_type)