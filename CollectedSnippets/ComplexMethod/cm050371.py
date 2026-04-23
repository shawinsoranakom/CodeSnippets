def create(self, vals_list):
        resources_vals_list = []
        calendar_ids = [vals['resource_calendar_id'] for vals in vals_list if vals.get('resource_calendar_id')]
        calendars_tz = {calendar.id: calendar.tz for calendar in self.env['resource.calendar'].browse(calendar_ids)}
        for vals in vals_list:
            if not vals.get('resource_id'):
                resources_vals_list.append(
                    self._prepare_resource_values(
                        vals,
                        vals.pop('tz', False) or calendars_tz.get(vals.get('resource_calendar_id'))
                    )
                )
        if resources_vals_list:
            resources = self.env['resource.resource'].create(resources_vals_list)
            resources_iter = iter(resources.ids)
            for vals in vals_list:
                if not vals.get('resource_id'):
                    vals['resource_id'] = next(resources_iter)
        return super(ResourceMixin, self.with_context(check_idempotence=True)).create(vals_list)