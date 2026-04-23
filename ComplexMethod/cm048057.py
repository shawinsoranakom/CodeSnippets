def _compute_request_hour_from_to(self):
        env_company_calendar = self.env.company.resource_calendar_id
        for leave in self:
            calendar = leave.resource_calendar_id or env_company_calendar
            if (not leave.request_unit_hours
                    and leave.employee_id
                    and leave.request_date_from
                    and leave.request_date_to
                    and calendar):
                hour_from, hour_to = leave._get_hour_from_to(leave.request_date_from, leave.request_date_to)
                leave.request_hour_from = hour_from
                leave.request_hour_to = hour_to