async def _async_get_event_config(
        self, http_fav: dict[str, dict[str, Any]]
    ) -> DoorbirdEventConfig:
        """Get events and unconfigured favorites from http favorites."""
        device = self.device
        events: list[DoorbirdEvent] = []
        unconfigured_favorites: defaultdict[str, list[str]] = defaultdict(list)
        try:
            schedule = await device.schedule()
        except ClientResponseError as ex:
            if ex.status == HTTPStatus.NOT_FOUND:
                # D301 models do not support schedules
                return DoorbirdEventConfig(events, [], unconfigured_favorites)
            raise
        favorite_input_type = {
            output.param: entry.input
            for entry in schedule
            for output in entry.output
            if output.event == HTTP_EVENT_TYPE
        }
        default_event_types = {
            self._get_event_name(event): event_type
            for event, event_type in DEFAULT_EVENT_TYPES
        }
        hass_url = self._get_hass_url()
        for identifier, data in http_fav.items():
            title: str | None = data.get("title")
            if not title or not title.startswith("Home Assistant"):
                continue
            value: str | None = data.get("value")
            if not value or not value.startswith(hass_url):
                continue  # Not our favorite - different HA instance or stale
            event = title.partition("(")[2].strip(")")
            if input_type := favorite_input_type.get(identifier):
                events.append(DoorbirdEvent(event, input_type))
            elif input_type := default_event_types.get(event):
                unconfigured_favorites[input_type].append(identifier)

        return DoorbirdEventConfig(events, schedule, unconfigured_favorites)