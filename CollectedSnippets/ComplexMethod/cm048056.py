def default_get(self, fields):
        defaults = super().default_get(fields)
        defaults = self._default_get_request_dates(defaults)
        if self.env.context.get('holiday_status_display_name', True) and 'holiday_status_id' in fields and not defaults.get('holiday_status_id'):
            domain = ['|', ('requires_allocation', '=', False), ('has_valid_allocation', '=', True)]
            defaults['holiday_status_id'] = False
            leave_types = self.env['hr.leave.type'].search(domain, order='sequence')
            selected_leave_type = next(
                (
                    leave_type for leave_type in leave_types
                    if (defaults.get('request_unit_hours') and leave_type['request_unit'] == 'hour') or (not defaults.get('request_unit_hours'))
                ),
                leave_types[0] if leave_types else None,
            )
            if selected_leave_type:
                defaults['holiday_status_id'] = selected_leave_type.id
                defaults['request_unit_hours'] = (selected_leave_type.request_unit == 'hour')

        if 'request_date_from' in fields and 'request_date_from' not in defaults:
            defaults['request_date_from'] = Date.today()
        if 'request_date_to' in fields and 'request_date_to' not in defaults:
            defaults['request_date_to'] = Date.today()

        return defaults