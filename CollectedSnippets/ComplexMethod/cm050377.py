def _get_valid_work_intervals(self, start, end, calendars=None, compute_leaves=True):
        """ Gets the valid work intervals of the resource following their calendars between ``start`` and ``end``

            This methods handle the eventuality of a resource having multiple resource calendars, see _get_calendars_validity_within_period method
            for further explanation.

            For flexible calendars and fully flexible resources: -> return the whole interval
        """
        assert start.tzinfo and end.tzinfo
        resource_calendar_validity_intervals = {}
        calendar_resources = defaultdict(lambda: self.env['resource.resource'])
        resource_work_intervals = defaultdict(Intervals)
        calendar_work_intervals = dict()

        resource_calendar_validity_intervals = self.sudo()._get_calendars_validity_within_period(start, end)
        for resource in self:
            # For each resource, retrieve its calendar and their validity intervals
            for calendar in resource_calendar_validity_intervals[resource.id]:
                calendar_resources[calendar] |= resource
        for calendar in (calendars or []):
            calendar_resources[calendar] |= self.env['resource.resource']
        for calendar, resources in calendar_resources.items():
            # for fully flexible resource, return the whole interval
            if not calendar:
                for resource in resources:
                    resource_work_intervals[resource.id] |= Intervals([(start, end, self.env['resource.calendar.attendance'])])
                continue
            # For each calendar used by the resources, retrieve the work intervals for every resources using it
            work_intervals_batch = calendar._work_intervals_batch(start, end, resources=resources, compute_leaves=compute_leaves)
            for resource in resources:
                # Make the conjunction between work intervals and calendar validity
                resource_work_intervals[resource.id] |= work_intervals_batch[resource.id] & resource_calendar_validity_intervals[resource.id][calendar]
            calendar_work_intervals[calendar.id] = work_intervals_batch[False]

        return resource_work_intervals, calendar_work_intervals