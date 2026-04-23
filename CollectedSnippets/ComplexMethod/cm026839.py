async def _async_update_data(self) -> CalendarEvent | None:
        """Get the latest data."""
        start_of_today = dt_util.start_of_local_day()
        start_of_tomorrow = dt_util.start_of_local_day() + timedelta(days=self.days)

        # We have to retrieve the results for the whole day as the server
        # won't return events that have already started
        results = await self.hass.async_add_executor_job(
            partial(
                self.calendar.search,
                start=start_of_today,
                end=start_of_tomorrow,
                event=True,
                expand=True,
            ),
        )

        # Create new events for each recurrence of an event that happens today.
        # For recurring events, some servers return the original event with recurrence rules
        # and they would not be properly parsed using their original start/end dates.
        new_events = []
        for event in results:
            if not hasattr(event.instance, "vevent"):
                _LOGGER.warning("Skipped event with missing 'vevent' property")
                continue
            vevent = event.instance.vevent
            for start_dt in vevent.getrruleset() or []:
                _start_of_today: date | datetime
                _start_of_tomorrow: datetime | date
                if self.is_all_day(vevent):
                    start_dt = start_dt.date()
                    _start_of_today = start_of_today.date()
                    _start_of_tomorrow = start_of_tomorrow.date()
                else:
                    _start_of_today = start_of_today
                    _start_of_tomorrow = start_of_tomorrow
                if _start_of_today <= start_dt < _start_of_tomorrow:
                    new_event = event.copy()
                    new_vevent = new_event.instance.vevent  # type: ignore[attr-defined]
                    if hasattr(new_vevent, "dtend"):
                        dur = new_vevent.dtend.value - new_vevent.dtstart.value
                        new_vevent.dtend.value = start_dt + dur
                    new_vevent.dtstart.value = start_dt
                    new_events.append(new_event)
                elif _start_of_tomorrow <= start_dt:
                    break
        vevents = [
            event.instance.vevent
            for event in results + new_events
            if hasattr(event.instance, "vevent")
        ]

        # dtstart can be a date or datetime depending if the event lasts a
        # whole day. Convert everything to datetime to be able to sort it
        vevents.sort(key=lambda x: self.to_datetime(x.dtstart.value))

        vevent = next(
            (
                vevent
                for vevent in vevents
                if (
                    self.is_matching(vevent, self.search)
                    and (not self.is_all_day(vevent) or self.include_all_day)
                    and not self.is_over(vevent)
                )
            ),
            None,
        )

        # If no matching event could be found
        if vevent is None:
            _LOGGER.debug(
                "No matching event found in the %d results for %s",
                len(vevents),
                self.calendar.name,
            )
            self.offset = None
            return None

        # Populate the entity attributes with the event values
        (summary, offset) = extract_offset(
            get_attr_value(vevent, "summary") or "", OFFSET
        )
        self.offset = offset
        return CalendarEvent(
            summary=summary,
            start=self.to_local(vevent.dtstart.value),
            end=self.to_local(self.get_end_date(vevent)),
            location=get_attr_value(vevent, "location"),
            description=get_attr_value(vevent, "description"),
        )