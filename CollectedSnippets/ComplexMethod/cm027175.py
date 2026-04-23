def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        next_waste_pickup_type = None
        next_waste_pickup_date = None
        for waste_type, waste_dates in self.coordinator.data.items():
            if (
                waste_dates
                and (
                    next_waste_pickup_date is None
                    or waste_dates[0] < next_waste_pickup_date
                )
                and waste_dates[0] >= dt_util.now().date()
            ):
                next_waste_pickup_date = waste_dates[0]
                next_waste_pickup_type = waste_type

        self._event = None
        if next_waste_pickup_date is not None and next_waste_pickup_type is not None:
            self._event = CalendarEvent(
                summary=WASTE_TYPE_TO_DESCRIPTION[next_waste_pickup_type],
                start=next_waste_pickup_date,
                end=next_waste_pickup_date + timedelta(days=1),
            )

        super()._handle_coordinator_update()