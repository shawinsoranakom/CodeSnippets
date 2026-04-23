async def async_handle_event(self, event_message: EventMessage) -> None:
        """Process an incoming EventMessage."""
        if not event_message.resource_update_name:
            return
        device_id = event_message.resource_update_name
        if not (events := event_message.resource_update_events):
            return
        _LOGGER.debug("Event Update %s", events.keys())
        device_registry = dr.async_get(self._hass)
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, device_id)}
        )
        if not device_entry:
            return
        supported_traits = self._supported_traits(device_id)
        for api_event_type, image_event in events.items():
            if not (event_type := EVENT_NAME_MAP.get(api_event_type)):
                continue
            nest_event_id = image_event.event_token
            message = {
                "device_id": device_entry.id,
                "type": event_type,
                "timestamp": event_message.timestamp,
                "nest_event_id": nest_event_id,
            }
            if (
                TraitType.CAMERA_EVENT_IMAGE in supported_traits
                or TraitType.CAMERA_CLIP_PREVIEW in supported_traits
            ):
                attachment = {
                    "image": EVENT_THUMBNAIL_URL_FORMAT.format(
                        device_id=device_entry.id, event_token=image_event.event_token
                    )
                }
                if TraitType.CAMERA_CLIP_PREVIEW in supported_traits:
                    attachment["video"] = EVENT_MEDIA_API_URL_FORMAT.format(
                        device_id=device_entry.id, event_token=image_event.event_token
                    )
                message["attachment"] = attachment
            if image_event.zones:
                message["zones"] = image_event.zones
            self._hass.bus.async_fire(NEST_EVENT, message)