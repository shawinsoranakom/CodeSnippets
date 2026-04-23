def _l10n_in_prepare_sandwich_context(self):
        """
            Build and return a tuple:
                (indian_leaves, leaves_by_employee, public_holidays_by_company_id)
            - Filters Indian, full-day, sandwich-enabled leaves.
            - Prepares dicts for sibling employee leaves and company public holidays.
        """
        def _to_local_date(datetime, tz):
            datetime = pytz.utc.localize(datetime, is_dst=False)
            return datetime.astimezone(tz).date()

        indian_leaves = self.filtered(
            lambda leave: leave.company_id.country_id.code == "IN"
            and leave.holiday_status_id.l10n_in_is_sandwich_leave
        )
        if not indian_leaves:
            return (indian_leaves, {}, {})

        leaves_dates_by_employee = {}
        grouped_leaves = self._read_group(
            domain=[
                ('id', 'not in', self.ids),
                ('employee_id', 'in', self.employee_id.ids),
                ('state', 'not in', ['cancel', 'refuse']),
                ('holiday_status_id.l10n_in_is_sandwich_leave', '=', True),
            ],
            groupby=['employee_id'],
            aggregates=['id:recordset'],
        )
        for emp_id, recs in grouped_leaves:
            valid_recs = recs.filtered(lambda leave: leave._l10n_in_is_full_day_request())
            if not valid_recs:
                continue
            leaves_dates_by_employee[emp_id] = {
                (leave.request_date_from + timedelta(days=offset)): leave
                for leave in valid_recs
                for offset in range((leave.request_date_to - leave.request_date_from).days + 1)
            }

        tz = pytz.timezone(self.env.context.get("tz") or self.env.user.tz or "UTC")
        public_holidays_dates_by_company = {}
        for company_id, recs in self.env['resource.calendar.leaves']._read_group(
            domain=[
                ('resource_id', '=', False),
                ('company_id', 'in', indian_leaves.company_id.ids),
            ],
            groupby=['company_id'],
            aggregates=['id:recordset'],
        ):
            company_dates = {}
            tz = pytz.timezone(company_id.resource_calendar_id.tz or self.env.context.get("tz") or self.env.user.tz or "UTC")
            for holiday in recs:
                local_start = _to_local_date(holiday.date_from, tz)
                local_end = _to_local_date(holiday.date_to, tz)
                for offset in range((local_end - local_start).days + 1):
                    company_dates[local_start + timedelta(days=offset)] = holiday
            public_holidays_dates_by_company[company_id] = company_dates
        return indian_leaves, leaves_dates_by_employee, public_holidays_dates_by_company