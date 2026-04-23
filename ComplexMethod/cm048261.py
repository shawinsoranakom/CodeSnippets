def _work_time_per_day(self, resource_calendars=False):
        """ Get work time per day based on the calendar and its attendances

            1) Gets all calendars with their characteristics (i.e.
                (a) the leaves in it,
                (b) the resources which have a leave,
                (c) the oldest and
                (d) the latest leave dates
               ) for leaves in self (first for calendar's leaves, then for company's global leaves)
            2) Search the attendances based on the characteristics retrieved for each calendar.
                The attendances found are the ones between the date_from of the oldest leave
                and the date_to of the most recent leave.
            3) Create a dict as result of this method containing:
                {
                    leave: {
                            max(date_start of work hours, date_start of the leave):
                                the duration in days of the work including the leave
                    }
                }
        """
        resource_calendars = resource_calendars or self._get_resource_calendars()
        # to easily find the calendar with its id.
        calendars_dict = {calendar.id: calendar for calendar in resource_calendars}

        leaves_read_group = self.env['resource.calendar.leaves']._read_group(
            [('id', 'in', self.ids), ('calendar_id', '!=', False)],
            ['calendar_id'],
            ['id:recordset', 'resource_id:recordset', 'date_from:min', 'date_to:max'],
        )
        # dict of keys: calendar_id
        #   and values : { 'date_from': datetime, 'date_to': datetime, resources: self.env['resource.resource'] }
        cal_attendance_intervals_dict = {}
        for calendar, leaves, resources, date_from_min, date_to_max in leaves_read_group:
            calendar_data = {
                'date_from': utc.localize(date_from_min),
                'date_to': utc.localize(date_to_max),
                'resources': resources,
                'leaves': leaves,
            }
            cal_attendance_intervals_dict[calendar.id] = calendar_data

        comp_leaves_read_group = self.env['resource.calendar.leaves']._read_group(
            [('id', 'in', self.ids), ('calendar_id', '=', False)],
            ['company_id'],
            ['id:recordset', 'resource_id:recordset', 'date_from:min', 'date_to:max'],
        )
        for company, leaves, resources, date_from_min, date_to_max in comp_leaves_read_group:
            for calendar_id in resource_calendars.ids:
                if (calendar_company := calendars_dict[calendar_id].company_id) and calendar_company != company:
                    continue  # only consider global leaves of the same company as the calendar
                calendar_data = cal_attendance_intervals_dict.get(calendar_id)
                if calendar_data is None:
                    calendar_data = {
                        'date_from': utc.localize(date_from_min),
                        'date_to': utc.localize(date_to_max),
                        'resources': resources,
                        'leaves': leaves,
                    }
                    cal_attendance_intervals_dict[calendar_id] = calendar_data
                else:
                    calendar_data.update(
                        date_from=min(utc.localize(date_from_min), calendar_data['date_from']),
                        date_to=max(utc.localize(date_to_max), calendar_data['date_to']),
                        resources=resources | calendar_data['resources'],
                        leaves=leaves | calendar_data['leaves'],
                    )

        # dict of keys: calendar_id
        #   and values: a dict of keys: leave.id
        #         and values: a dict of keys: date
        #              and values: number of days
        results = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        for calendar_id, cal_attendance_intervals_params_entry in cal_attendance_intervals_dict.items():
            calendar = calendars_dict[calendar_id]
            work_hours_intervals = calendar._attendance_intervals_batch(
                cal_attendance_intervals_params_entry['date_from'],
                cal_attendance_intervals_params_entry['date_to'],
                cal_attendance_intervals_params_entry['resources'],
                tz=timezone(calendar.tz)
            )
            for leave in cal_attendance_intervals_params_entry['leaves']:
                work_hours_data = work_hours_intervals[leave.resource_id.id]

                for date_from, date_to, _dummy in work_hours_data:
                    if date_to > utc.localize(leave.date_from) and date_from < utc.localize(leave.date_to):
                        tmp_start = max(date_from, utc.localize(leave.date_from))
                        tmp_end = min(date_to, utc.localize(leave.date_to))
                        results[calendar_id][leave.id][tmp_start.date()] += (tmp_end - tmp_start).total_seconds() / 3600
                results[calendar_id][leave.id] = sorted(results[calendar_id][leave.id].items())
        return results