def _compute_dashboard_warning_message(self):
        all_leaves = self.search([
            ('date_from', '<', max(self.mapped('date_to'))),
            ('date_to', '>', min(self.mapped('date_from'))),
            ('employee_id', 'in', self.employee_id.ids),
            ('holiday_status_id.allow_request_on_top', '=', False),
            ('state', 'not in', ['cancel', 'refuse']),
        ])
        self.filtered(lambda self: self.state in ['cancel', 'refuse']).dashboard_warning_message = False
        for holiday in self.filtered(lambda self: self.state not in ['cancel', 'refuse']):
            conflicting_holidays = all_leaves.filtered_domain([
                ('employee_id', 'in', holiday.employee_id.ids),
                ('date_from', '<', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('id', 'not in', holiday.ids),
            ])
            if not conflicting_holidays:
                holiday.dashboard_warning_message = False
                continue

            conflicting_holidays_list = []
            # Do not display the name of the employee if the conflicting holidays have an employee_id.user_id equivalent to the user id
            holidays_only_have_uid = bool(holiday.employee_id)
            holiday_states = dict(conflicting_holidays.fields_get(allfields=['state'])['state']['selection'])
            for conflicting_holiday in conflicting_holidays:
                conflicting_holiday_data = {
                    'employee_name': conflicting_holiday.employee_id.name,
                    'date_from': format_date(self.env, min(conflicting_holiday.mapped('date_from'))),
                    'date_to': format_date(self.env, min(conflicting_holiday.mapped('date_to'))),
                    'state': holiday_states[conflicting_holiday.state]
                }
                if conflicting_holiday.employee_id.user_id.id != self.env.uid:
                    holidays_only_have_uid = False
                if conflicting_holiday_data not in conflicting_holidays_list:
                    conflicting_holidays_list.append(conflicting_holiday_data)

            msg = ""
            if holidays_only_have_uid:
                msg = self.env._('You\'ve already booked time off which overlaps with this period:')
            else:
                msg = self.env._('An employee already booked time off which overlaps with this period:')

            holiday.dashboard_warning_message = msg + "".join(
                ('\n\t' + self.env._('%(employee_name)s from %(date_from)s to %(date_to)s - %(state)s')) % {
                    'employee_name': conflicting_holiday_data['employee_name'] if not holidays_only_have_uid else "",
                    'date_from': conflicting_holiday_data['date_from'],
                    'date_to': conflicting_holiday_data['date_to'],
                    'state': conflicting_holiday_data['state']
                } for conflicting_holiday_data in conflicting_holidays_list
            )