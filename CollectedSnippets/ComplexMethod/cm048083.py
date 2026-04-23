def _get_first_working_interval(self, dt):
        # find the first working interval after a given date
        dt = dt.replace(tzinfo=timezone.utc)
        lookahead_days = [7, 30, 90, 180, 365, 730]
        work_intervals = None
        for lookahead_day in lookahead_days:
            periods = self._get_calendar_periods(dt, dt + timedelta(days=lookahead_day))
            if not periods:
                calendar = self.resource_calendar_id or self.company_id.resource_calendar_id
                work_intervals = calendar._work_intervals_batch(
                    dt, dt + timedelta(days=lookahead_day), resources=self.resource_id)
            else:
                for period in periods[self]:
                    start, end, calendar = period
                    calendar = calendar or self.company_id.resource_calendar_id
                    work_intervals = calendar._work_intervals_batch(
                        start, end, resources=self.resource_id)
            if work_intervals.get(self.resource_id.id) and work_intervals[self.resource_id.id]._items:
                # return start time of the earliest interval
                return work_intervals[self.resource_id.id]._items[0][0]