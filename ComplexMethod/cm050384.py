def _get_closest_work_time(self, dt, match_end=False, resource=None, search_range=None, compute_leaves=True):
        """Return the closest work interval boundary within the search range.
        Consider only starts of intervals unless `match_end` is True. It will then only consider
        ends of intervals.
        :param dt: reference datetime
        :param match_end: wether to search for the begining of an interval or the end.
        :param search_range: time interval considered. Defaults to the entire day of `dt`
        :rtype: datetime | None
        """
        def interval_dt(interval):
            return interval[1 if match_end else 0]

        tz = resource.tz if resource else self.tz
        if resource is None:
            resource = self.env['resource.resource']

        if not dt.tzinfo or (search_range and not (search_range[0].tzinfo and search_range[1].tzinfo)):
            raise ValueError(self.env._('Provided datetimes needs to be timezoned'))

        dt = dt.astimezone(timezone(tz))

        if not search_range:
            range_start = dt + relativedelta(hour=0, minute=0, second=0)
            range_end = dt + relativedelta(days=1, hour=0, minute=0, second=0)
        else:
            range_start, range_end = search_range

        if not range_start <= dt <= range_end:
            return None
        work_intervals = sorted(
            self._work_intervals_batch(range_start, range_end, resource, compute_leaves=compute_leaves)[resource.id],
            key=lambda i: abs(interval_dt(i) - dt),
        )
        return interval_dt(work_intervals[0]) if work_intervals else None