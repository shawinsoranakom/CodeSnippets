def _get_version_periods(self, start, stop, field=None, check_contract=False):
        if field and field not in self:
            raise UserError(self.env._(
                "This field %(field_name)s doesn't exist on this model (hr.version).",
                field_name=field
            ))
        version_periods_by_employee = defaultdict(list)
        if check_contract:
            versions = self._get_versions_with_contract_overlap_with_period(start.date(), stop.date())
        else:
            versions = self.version_ids.filtered_domain([
                ('date_start', '<=', stop),
                '|',
                    ('date_end', '=', False),
                    ('date_end', '>=', start)
            ])
        for version in versions:
            # if employee is under fully flexible contract, use timezone of the employee
            calendar_tz = timezone(version.resource_calendar_id.tz) if version.resource_calendar_id else timezone(version.employee_id.resource_id.tz)
            date_start = datetime.combine(version.date_start, time.min).replace(tzinfo=calendar_tz).astimezone(utc)
            end_date = version.date_end
            if end_date:
                date_end = datetime.combine(
                    end_date + relativedelta(days=1),
                    time.min,
                ).replace(tzinfo=calendar_tz).astimezone(utc)
            else:
                date_end = stop
            version_periods_by_employee[version.employee_id].append(
                (max(date_start, start), min(date_end, stop), version[field] if field else version))
        return version_periods_by_employee