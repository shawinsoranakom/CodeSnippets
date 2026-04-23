def _get_calendars_validity_within_period(self, start, end, default_company=None):
        """ Gets a dict of dict with resource's id as first key and resource's calendar as secondary key
            The value is the validity interval of the calendar for the given resource.

            Here the validity interval for each calendar is the whole interval but it's meant to be overriden in further modules
            handling resource's employee contracts.
        """
        assert start.tzinfo and end.tzinfo
        resource_calendars_within_period = defaultdict(lambda: defaultdict(Intervals))  # keys are [resource id:integer][calendar:self.env['resource.calendar']]
        default_calendar = default_company and default_company.resource_calendar_id or self.env.company.resource_calendar_id
        if not self:
            # if no resource, add the company resource calendar.
            resource_calendars_within_period[False][default_calendar] = Intervals([(start, end, self.env['resource.calendar.attendance'])])
        for resource in self:
            calendar = resource.calendar_id or resource.company_id.resource_calendar_id or default_calendar
            resource_calendars_within_period[resource.id][calendar] = Intervals([(start, end, self.env['resource.calendar.attendance'])])
        return resource_calendars_within_period