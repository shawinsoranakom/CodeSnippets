def _get_contracts_valid_periods(self, start, end):
        res = defaultdict(lambda: defaultdict(Intervals))
        timezones = {resource.tz for resource in self}
        date_start = min(start.astimezone(timezone(tz)).date() for tz in timezones)
        date_end = max(end.astimezone(timezone(tz)).date() for tz in timezones)
        contracts = self.employee_id._get_versions_with_contract_overlap_with_period(date_start, date_end)
        for contract in contracts:
            tz = timezone(contract.employee_id.tz)
            res[contract.employee_id.resource_id.id][contract.resource_calendar_id] |= Intervals([(
                tz.localize(datetime.combine(contract.contract_date_start, datetime.min.time())) if contract.contract_date_start > start.astimezone(tz).date() else start,
                tz.localize(datetime.combine(contract.contract_date_end, datetime.max.time())) if contract.contract_date_end and contract.contract_date_end < end.astimezone(tz).date() else end,
                self.env['resource.calendar.attendance']
            )])
        return res