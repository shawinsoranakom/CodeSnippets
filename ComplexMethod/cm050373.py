def _get_leave_days_data_batch(self, from_datetime, to_datetime, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the number of leaves
            expressed as days and as hours.
        """
        resources = self.mapped('resource_id')
        mapped_employees = {e.resource_id.id: e.id for e in self}
        result = {}

        # naive datetimes are made explicit in UTC
        from_datetime = localized(from_datetime)
        to_datetime = localized(to_datetime)

        mapped_resources = defaultdict(lambda: self.env['resource.resource'])
        for record in self:
            mapped_resources[calendar or record.resource_calendar_id] |= record.resource_id

        for calendar, calendar_resources in mapped_resources.items():
            # handle fully flexible resources by returning the length of the whole interval
            # since we do not take into account leaves for fully flexible resources
            if not calendar:
                days = (to_datetime - from_datetime).days
                hours = (to_datetime - from_datetime).total_seconds() / 3600
                for calendar_resource in calendar_resources:
                    result[calendar_resource.id] = {'days': days, 'hours': hours}
                continue

            # compute actual hours per day
            attendances = calendar._attendance_intervals_batch(from_datetime, to_datetime, calendar_resources)
            leaves = calendar._leave_intervals_batch(from_datetime, to_datetime, calendar_resources, domain)

            for calendar_resource in calendar_resources:
                result[calendar_resource.id] = calendar._get_attendance_intervals_days_data(
                    attendances[calendar_resource.id] & leaves[calendar_resource.id]
                )

        # convert "resource: result" into "employee: result"
        return {mapped_employees[r.id]: result[r.id] for r in resources}