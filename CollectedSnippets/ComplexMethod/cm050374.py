def _list_work_time_per_day(self, from_datetime, to_datetime, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a list of tuples (day, hours) for each day
            containing at least an attendance.
        """
        result = {}
        records_by_calendar = defaultdict(lambda: self.env[self._name])
        for record in self:
            records_by_calendar[calendar or record.resource_calendar_id or record.company_id.resource_calendar_id] += record

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)
        compute_leaves = self.env.context.get('compute_leaves', True)

        for calendar, records in records_by_calendar.items():
            resources = self.resource_id
            all_intervals = calendar._work_intervals_batch(from_datetime, to_datetime, resources, domain, compute_leaves=compute_leaves)
            for record in records:
                intervals = all_intervals[record.resource_id.id]
                record_result = defaultdict(float)
                for start, stop, _meta in intervals:
                    record_result[start.date()] += (stop - start).total_seconds() / 3600
                result[record.id] = sorted(record_result.items())
        return result