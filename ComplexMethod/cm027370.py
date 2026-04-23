async def _async_update_data(self) -> TrainData:
        """Fetch data from Trafikverket."""

        when = dt_util.now()
        state: TrainStopModel | None = None
        states: list[TrainStopModel] | None = None
        if self._time:
            departure_day = next_departuredate(self._weekdays)
            when = datetime.combine(
                departure_day,
                self._time,
                dt_util.get_default_time_zone(),
            )
        try:
            if self._time:
                state = await self._train_api.async_get_train_stop(
                    self.from_station, self.to_station, when, self._filter_product
                )
            else:
                states = await self._train_api.async_get_next_train_stops(
                    self.from_station,
                    self.to_station,
                    when,
                    self._filter_product,
                    number_of_stops=3,
                )
        except InvalidAuthentication as error:
            raise ConfigEntryAuthFailed from error
        except (
            NoTrainAnnouncementFound,
            UnknownError,
        ) as error:
            raise UpdateFailed(
                f"Train departure {when} encountered a problem: {error}"
            ) from error

        depart_next = None
        depart_next_next = None
        if not state and states:
            state = states[0]
            depart_next = (
                states[1].advertised_time_at_location if len(states) > 1 else None
            )
            depart_next_next = (
                states[2].advertised_time_at_location if len(states) > 2 else None
            )

        if not state:
            raise UpdateFailed("Could not find any departures")

        departure_time = state.advertised_time_at_location
        if state.estimated_time_at_location:
            departure_time = state.estimated_time_at_location
        elif state.time_at_location:
            departure_time = state.time_at_location

        delay_time = state.get_delay_time()

        return TrainData(
            departure_time=_get_as_utc(departure_time),
            departure_state=state.get_state().value,
            cancelled=state.canceled,
            delayed_time=delay_time.seconds if delay_time else None,
            planned_time=_get_as_utc(state.advertised_time_at_location),
            estimated_time=_get_as_utc(state.estimated_time_at_location),
            actual_time=_get_as_utc(state.time_at_location),
            other_info=_get_as_joined(state.other_information),
            deviation=_get_as_joined(state.deviations),
            product_filter=self._filter_product,
            departure_time_next=_get_as_utc(depart_next),
            departure_time_next_next=_get_as_utc(depart_next_next),
        )