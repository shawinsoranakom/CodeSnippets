def _check_dates(self):
        version_read_group = self.env['hr.version'].sudo()._read_group(
            [
                ('id', 'not in', self.ids),
                ('employee_id', 'in', self.employee_id.ids),
                ('contract_date_start', '!=', False),
            ],
            ['employee_id', 'contract_date_start:day', 'contract_date_end:day'],
            ['id:recordset'],
        )
        dates_per_employee = defaultdict(list)
        for employee, date_start, date_end, versions in version_read_group:
            dates_per_employee[employee].append((date_start, date_end, versions))
        for version in self.sudo():  # sudo needed to read contract dates
            if not version.contract_date_start or not version.employee_id:
                continue
            if version.contract_date_end and version.contract_date_start > version.contract_date_end:
                raise ValidationError(self.env._(
                    'Start date (%(start)s) must be earlier than contract end date (%(end)s).',
                    start=version.contract_date_start, end=version.contract_date_end,
                ))
            if not version.active:
                continue
            contract_date_end = version.contract_date_end or date.max
            contract_period_exists = False
            for date_start, date_end, versions in dates_per_employee[version.employee_id]:
                date_to = date_end or date.max
                if date_start == version.contract_date_start and date_to == contract_date_end:
                    contract_period_exists = True
                    continue
                if date_start <= contract_date_end and version.contract_date_start <= date_to:
                    raise ValidationError(self.env._(
                        "%s already has a contract running during the selected period.\n\n"
                        "Please either:\n\n"
                        "- Change the start date so that it doesn't overlap with the existing contract, or\n"
                        "- Create a new employee if this employee should have multiple active contracts.",
                        version.employee_id.display_name))
            if not contract_period_exists:
                dates_per_employee[version.employee_id].append((version.contract_date_start, version.contract_date_end, version))