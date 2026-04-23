def _get_expected_attendances(self, date_from, date_to):
        self.ensure_one()
        valid_versions = self.sudo()._get_versions_with_contract_overlap_with_period(date_from.date(), date_to.date())
        employee_tz = timezone(self.tz) if self.tz else None
        if not valid_versions:
            calendar = self.resource_calendar_id or self.company_id.resource_calendar_id
            calendar_intervals = calendar._work_intervals_batch(
                date_from,
                date_to,
                tz=employee_tz,
                resources=self.resource_id,
                compute_leaves=True,
                domain=[('company_id', 'in', [False, self.company_id.id])])[self.resource_id.id]
            return calendar_intervals
        duration_data = Intervals()
        version_prev = datetime.combine(valid_versions[0].date_start, time.min, employee_tz)
        for version in valid_versions:
            version_start = datetime.combine(version.date_start, time.min, employee_tz)
            contract_start = datetime.combine(version.contract_date_start, time.min, employee_tz)
            version_end = datetime.combine(version.date_end or date.max, time.max, employee_tz)
            calendar = version.resource_calendar_id or version.company_id.resource_calendar_id
            start_date = version_start if version_prev < version_start else contract_start
            version_intervals = calendar._work_intervals_batch(
                                    max(date_from, start_date),
                                    min(date_to, version_end),
                                    tz=employee_tz,
                                    resources=self.resource_id,
                                    compute_leaves=True,
                                    domain=[('company_id', 'in', [False, self.company_id.id]), ('time_type', '=', 'leave')])[self.resource_id.id]
            duration_data = duration_data | version_intervals
        return duration_data