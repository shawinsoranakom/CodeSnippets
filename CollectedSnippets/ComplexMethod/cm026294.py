async def _get_camera_thumbnail_url(self, camera: Camera) -> str | None:
        """Get camera thumbnail URL using the first available camera entity."""

        if not camera.is_connected or camera.is_privacy_on:
            return None

        entity_id: str | None = None
        entity_registry = self.async_get_registry()
        for channel in camera.channels:
            # do not use the package camera
            if channel.id == 3:
                continue

            base_id = f"{camera.mac}_{channel.id}"
            entity_id = entity_registry.async_get_entity_id(
                Platform.CAMERA, DOMAIN, base_id
            )
            if entity_id is None:
                entity_id = entity_registry.async_get_entity_id(
                    Platform.CAMERA, DOMAIN, f"{base_id}_insecure"
                )

            if entity_id:
                # verify entity is available
                entry = entity_registry.async_get(entity_id)
                if entry and not entry.disabled:
                    break
                entity_id = None

        if entity_id is not None:
            url = URL(CameraImageView.url.format(entity_id=entity_id))
            return str(
                url.update_query({"width": THUMBNAIL_WIDTH, "height": THUMBNAIL_HEIGHT})
            )
        return None