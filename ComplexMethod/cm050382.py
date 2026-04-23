def _leave_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None):
        """ Return the leave intervals in the given datetime range.
            The returned intervals are expressed in specified tz or in the calendar's timezone.
        """
        assert start_dt.tzinfo and end_dt.tzinfo

        if not resources:
            resources = self.env['resource.resource']
            resources_list = [resources]
        else:
            resources_list = list(resources) + [self.env['resource.resource']]
        if domain is None:
            domain = [('time_type', '=', 'leave')]
        if self:
            domain = domain + [('calendar_id', 'in', [False] + self.ids)]

        # for the computation, express all datetimes in UTC
        # Public leave don't have a resource_id
        domain = domain + [
            ('resource_id', 'in', [False] + [r.id for r in resources_list]),
            ('date_from', '<=', end_dt.astimezone(utc).replace(tzinfo=None)),
            ('date_to', '>=', start_dt.astimezone(utc).replace(tzinfo=None)),
        ]

        # retrieve leave intervals in (start_dt, end_dt)
        result = defaultdict(list)
        tz_dates = {}
        all_leaves = self.env['resource.calendar.leaves'].search(domain)
        for leave in all_leaves:
            leave_resource = leave.resource_id
            leave_company = leave.company_id
            leave_date_from = leave.date_from
            leave_date_to = leave.date_to
            for resource in resources_list:
                if leave_resource.id not in [False, resource.id] or (not leave_resource and resource and resource.company_id != leave_company):
                    continue
                tz = tz if tz else timezone((resource or self).tz)
                if (tz, start_dt) in tz_dates:
                    start = tz_dates[tz, start_dt]
                else:
                    start = start_dt.astimezone(tz)
                    tz_dates[tz, start_dt] = start
                if (tz, end_dt) in tz_dates:
                    end = tz_dates[tz, end_dt]
                else:
                    end = end_dt.astimezone(tz)
                    tz_dates[tz, end_dt] = end
                dt0 = leave_date_from.astimezone(tz)
                dt1 = leave_date_to.astimezone(tz)
                if leave_resource and leave_resource._is_fully_flexible():
                    dt0, dt1 = self._handle_flexible_leave_interval(dt0, dt1, leave)
                result[resource.id].append((max(start, dt0), min(end, dt1), leave))

        return {r.id: Intervals(result[r.id]) for r in resources_list}