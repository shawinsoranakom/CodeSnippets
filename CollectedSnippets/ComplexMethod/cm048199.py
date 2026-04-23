def _prepare_calendar_values(self, event):
        """ This methods slit the day (max end time - min start time) into
        15 minutes time slots. For each time slot, we assign the tracks that
        start at this specific time slot, and we add the number of time slot
        that the track covers (track duration / 15 min). The calendar will be
        divided into rows of 15 min, and the talks will cover the corresponding
        number of rows (15 min slots). """
        event = event.with_context(tz=event.date_tz or 'UTC')
        local_tz = pytz.timezone(event.date_tz or 'UTC')
        lang_code = request.env.context.get('lang')

        base_track_domain = Domain.AND([
            self._get_event_tracks_agenda_domain(event),
            [('date', '!=', False)]
        ])
        tracks_sudo = request.env['event.track'].sudo().search(base_track_domain)

        locations = list(set(track.location_id for track in tracks_sudo))
        locations.sort(key=operator.itemgetter('sequence', 'id'))

        # First split day by day (based on start time)
        time_slots_by_tracks = {track: self._split_track_by_days(track, local_tz) for track in tracks_sudo}

        # extract all the tracks time slots
        track_time_slots = set().union(*(time_slot.keys() for time_slot in [time_slots for time_slots in time_slots_by_tracks.values()]))

        # extract unique days
        days = list(set(time_slot.date() for time_slot in track_time_slots))
        days.sort()

        # Create the dict that contains the tracks at the correct time_slots / locations coordinates
        tracks_by_days = dict.fromkeys(days, 0)
        time_slots_by_day = dict((day, dict(start=set(), end=set())) for day in days)
        tracks_by_rounded_times = dict((time_slot, dict((location, {}) for location in locations)) for time_slot in track_time_slots)
        for track, time_slots in time_slots_by_tracks.items():
            start_date = fields.Datetime.from_string(track.date).replace(tzinfo=pytz.utc).astimezone(local_tz)
            end_date = start_date + timedelta(hours=(track.duration or 0.25))

            for time_slot, duration in time_slots.items():
                tracks_by_rounded_times[time_slot][track.location_id][track] = {
                    'rowspan': duration,  # rowspan
                    'start_date': self._get_locale_time(start_date, lang_code),
                    'end_date': self._get_locale_time(end_date, lang_code),
                    'occupied_cells': self._get_occupied_cells(track, duration, locations, local_tz)
                }

                # get all the time slots by day to determine the max duration of a day.
                day = time_slot.date()
                time_slots_by_day[day]['start'].add(time_slot)
                time_slots_by_day[day]['end'].add(time_slot+timedelta(minutes=15*duration))
                tracks_by_days[day] += 1

        # split days into 15 minutes time slots
        global_time_slots_by_day = dict((day, {}) for day in days)
        for day, time_slots in time_slots_by_day.items():
            start_time_slot = min(time_slots['start'])
            end_time_slot = max(time_slots['end'])

            time_slots_count = int(((end_time_slot - start_time_slot).total_seconds() / 3600) * 4)
            current_time_slot = start_time_slot
            for _i in range(0, time_slots_count + 1):
                global_time_slots_by_day[day][current_time_slot] = tracks_by_rounded_times.get(current_time_slot, {})
                global_time_slots_by_day[day][current_time_slot]['formatted_time'] = self._get_locale_time(current_time_slot, lang_code)
                current_time_slot = current_time_slot + timedelta(minutes=15)

        # count the number of tracks by days
        tracks_by_days = dict.fromkeys(days, 0)
        locations_by_days = defaultdict(list)
        for track in tracks_sudo:
            track_day = fields.Datetime.from_string(track.date).replace(tzinfo=pytz.utc).astimezone(local_tz).date()
            tracks_by_days[track_day] += 1
            if track.location_id not in locations_by_days[track_day]:
                locations_by_days[track_day].append(track.location_id)

        for used_locations in locations_by_days.values():
            used_locations.sort(key=operator.itemgetter('sequence', 'id'))

        return {
            'days': days,
            'tracks_by_days': tracks_by_days,
            'locations_by_days': locations_by_days,
            'time_slots': global_time_slots_by_day,
            'locations': locations  # TODO: clean me in master, kept for retro-compatibility
        }