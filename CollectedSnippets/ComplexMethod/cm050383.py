def _unavailable_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None):
        """ Return the unavailable intervals between the given datetimes. """
        if not resources:
            resources = self.env['resource.resource']
            resources_list = [resources]
        else:
            resources_list = list(resources)

        resources_work_intervals = self._work_intervals_batch(start_dt, end_dt, resources, domain, tz)
        result = {}
        for resource in resources_list:
            if resource and resource._is_flexible():
                leaves = self._leave_intervals_batch(start_dt, end_dt, resource, domain, tz=tz)
                if res_leaves := leaves.get(resource.id, []):
                    result[resource.id] = [(i[0], i[1]) for i in res_leaves]
                continue
            work_intervals = [(start, stop) for start, stop, meta in resources_work_intervals[resource.id]]
            # start + flatten(intervals) + end
            work_intervals = [start_dt] + list(chain.from_iterable(work_intervals)) + [end_dt]
            # put it back to UTC
            work_intervals = [dt.astimezone(utc) for dt in work_intervals]
            # pick groups of two
            work_intervals = list(zip(work_intervals[0::2], work_intervals[1::2]))
            result[resource.id] = work_intervals
        return result