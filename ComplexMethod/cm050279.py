def _employee_attendance_intervals(self, start, stop, lunch=False):
        self.ensure_one()
        if not lunch:
            return self._get_expected_attendances(start, stop)
        else:
            valid_versions = self.sudo()._get_versions_with_contract_overlap_with_period(start.date(), stop.date())
            if not valid_versions:
                calendar = self.resource_calendar_id or self.company_id.resource_calendar_id
                return calendar._attendance_intervals_batch(start, stop, self.resource_id, lunch=True)[self.resource_id.id]
            employee_tz = timezone(self.tz) if self.tz else None
            duration_data = Intervals()
            for version in valid_versions:
                version_start = datetime.combine(version.date_start, time.min, employee_tz)
                version_end = datetime.combine(version.date_end or date.max, time.max, employee_tz)
                calendar = version.resource_calendar_id or version.company_id.resource_calendar_id
                lunch_intervals = calendar._attendance_intervals_batch(
                    max(start, version_start),
                    min(stop, version_end),
                    resources=self.resource_id,
                    lunch=True)[self.resource_id.id]
                duration_data = duration_data | lunch_intervals
            return duration_data