def update_entity_trigger(
        entity_id: str, new_state: State | None = None, offset: timedelta = timedelta(0)
    ) -> None:
        """Update the entity trigger for the entity_id."""
        # If a listener was already set up for entity, remove it.
        if remove := entities.pop((entity_id, offset), None):
            remove()
            remove = None

        if not new_state:
            return

        trigger_dt: datetime | None

        # Check state of entity. If valid, set up a listener.
        if new_state.domain == "input_datetime":
            if has_date := new_state.attributes["has_date"]:
                year = new_state.attributes["year"]
                month = new_state.attributes["month"]
                day = new_state.attributes["day"]
            if has_time := new_state.attributes["has_time"]:
                hour = new_state.attributes["hour"]
                minute = new_state.attributes["minute"]
                second = new_state.attributes["second"]
            else:
                # If no time then use midnight.
                hour = minute = second = 0

            if has_date:
                # If input_datetime has date, then track point in time.
                trigger_dt = (
                    datetime(
                        year,
                        month,
                        day,
                        hour,
                        minute,
                        second,
                        tzinfo=dt_util.get_default_time_zone(),
                    )
                    + offset
                )
                # Only set up listener if time is now or in the future.
                if trigger_dt >= dt_util.now():
                    remove = async_track_point_in_time(
                        hass,
                        partial(
                            time_automation_listener,
                            f"time set in {entity_id}",
                            entity_id=entity_id,
                        ),
                        trigger_dt,
                    )
            elif has_time:
                # Else if it has time, then track time change.
                if offset != timedelta(0):
                    # Create a temporary datetime object to get an offset.
                    temp_dt = dt_util.now().replace(
                        hour=hour, minute=minute, second=second, microsecond=0
                    )
                    temp_dt += offset
                    # Ignore the date and apply the offset even if it wraps
                    # around to the next day.
                    hour = temp_dt.hour
                    minute = temp_dt.minute
                    second = temp_dt.second
                remove = async_track_time_change(
                    hass,
                    partial(
                        time_automation_listener,
                        f"time set in {entity_id}",
                        entity_id=entity_id,
                    ),
                    hour=hour,
                    minute=minute,
                    second=second,
                )
        elif (
            new_state.domain == "sensor"
            and new_state.attributes.get(ATTR_DEVICE_CLASS)
            == sensor.SensorDeviceClass.TIMESTAMP
            and new_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
        ):
            trigger_dt = dt_util.parse_datetime(new_state.state)

            if trigger_dt is not None:
                trigger_dt += offset

            if trigger_dt is not None and trigger_dt > dt_util.utcnow():
                remove = async_track_point_in_time(
                    hass,
                    partial(
                        time_automation_listener,
                        f"time set in {entity_id}",
                        entity_id=entity_id,
                    ),
                    trigger_dt,
                )

        # Was a listener set up?
        if remove:
            entities[(entity_id, offset)] = remove