def plan_hours(self, hours, day_dt, compute_leaves=False, domain=None, resource=None):
        """
        `compute_leaves` controls whether or not this method is taking into
        account the global leaves.

        `domain` controls the way leaves are recognized.
        None means default value ('time_type', '=', 'leave')

        Return datetime after having planned hours
        """
        revert = to_timezone(day_dt.tzinfo)
        day_dt = localized(day_dt)

        if resource is None:
            resource = self.env['resource.resource']

        # which method to use for retrieving intervals
        if compute_leaves:
            get_intervals = partial(self._work_intervals_batch, domain=domain, resources=resource)
            resource_id = resource.id
        else:
            get_intervals = self._attendance_intervals_batch
            resource_id = False

        if hours >= 0:
            delta = timedelta(days=14)
            for n in range(100):
                dt = day_dt + delta * n
                for start, stop, _meta in get_intervals(dt, dt + delta)[resource_id]:
                    interval_hours = (stop - start).total_seconds() / 3600
                    if hours <= interval_hours:
                        return revert(start + timedelta(hours=hours))
                    hours -= interval_hours
            return False
        hours = abs(hours)
        delta = timedelta(days=14)
        for n in range(100):
            dt = day_dt - delta * n
            for start, stop, _meta in reversed(get_intervals(dt - delta, dt)[resource_id]):
                interval_hours = (stop - start).total_seconds() / 3600
                if hours <= interval_hours:
                    return revert(stop - timedelta(hours=hours))
                hours -= interval_hours
        return False