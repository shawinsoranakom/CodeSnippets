async def get(
        self, request: web.Request, datetime: str | None = None
    ) -> web.Response:
        """Retrieve logbook entries."""
        if datetime:
            if (datetime_dt := dt_util.parse_datetime(datetime)) is None:
                return self.json_message("Invalid datetime", HTTPStatus.BAD_REQUEST)
        else:
            datetime_dt = dt_util.start_of_local_day()

        if (period_str := request.query.get("period")) is None:
            period: int = 1
        else:
            period = int(period_str)

        if entity_ids_str := request.query.get("entity"):
            try:
                entity_ids = cv.entity_ids(entity_ids_str)
            except vol.Invalid as ex:
                raise InvalidEntityFormatError(
                    f"Invalid entity id(s) encountered: {entity_ids_str}. "
                    "Format should be <domain>.<object_id>"
                ) from ex
        else:
            entity_ids = None

        if (end_time_str := request.query.get("end_time")) is None:
            start_day = dt_util.as_utc(datetime_dt) - timedelta(days=period - 1)
            end_day = start_day + timedelta(days=period)
        else:
            start_day = datetime_dt
            if (end_day_dt := dt_util.parse_datetime(end_time_str)) is None:
                return self.json_message("Invalid end_time", HTTPStatus.BAD_REQUEST)
            end_day = end_day_dt

        hass = request.app[KEY_HASS]

        context_id = request.query.get("context_id")

        if entity_ids and context_id:
            return self.json_message(
                "Can't combine entity with context_id", HTTPStatus.BAD_REQUEST
            )

        event_types = async_determine_event_types(hass, entity_ids, None)
        event_processor = EventProcessor(
            hass,
            event_types,
            entity_ids,
            None,
            context_id,
            timestamp=False,
            include_entity_name=True,
        )

        def json_events() -> web.Response:
            """Fetch events and generate JSON."""
            return self.json(event_processor.get_events(start_day, end_day))

        return await get_instance(hass).async_add_executor_job(json_events)