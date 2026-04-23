def create_version(self, values):
        self.ensure_one()

        date = values.get('date_version', False)
        if not date:
            raise ValueError("date_version is required")

        if isinstance(date, str):
            date = fields.Date.to_date(date)
        elif isinstance(date, datetime):
            date = date.date()

        version_to_copy = self._get_version(date)
        if not version_to_copy:
            version_to_copy = self.env['hr.version'].search([('employee_id', '=', self.id)], limit=1)
        if version_to_copy.date_version == date:
            return version_to_copy

        date_from, date_to = self.sudo()._get_contract_dates(date)
        contract_date_start = values.get('contract_date_start', date_from)
        contract_date_end = values.get('contract_date_end', date_to)
        employee_id = values.get('employee_id', self.id)

        if isinstance(contract_date_start, str):
            contract_date_start = fields.Date.to_date(contract_date_start)
        if isinstance(contract_date_end, str):
            contract_date_end = fields.Date.to_date(contract_date_end)

        if contract_date_start == date_from and contract_date_end != date_to:
            versions_sudo_to_sync = self.env['hr.version'].with_context(sync_contract_dates=True).sudo().search([
                ('employee_id', '=', employee_id),
                ('contract_date_start', '=', date_from),
            ])
            if versions_sudo_to_sync:
                versions_sudo_to_sync.write({
                    'contract_date_end': contract_date_end,
                })
        self.check_access('write')
        version_to_copy.check_access('write')
        # to be sure even if the user has no access to certain fields, we can still copy the verison without any issues.
        copy_vals = {
            'date_version': date,
            'employee_id': employee_id,
            'contract_date_start': contract_date_start,
            'contract_date_end': contract_date_end,
        }
        if 'active' in values:
            copy_vals['active'] = values['active']
        if calendar_id := values.get('resource_calendar_id'):
            copy_vals['resource_calendar_id'] = calendar_id
        # apply the changes on the new versions.
        new_version_vals = {
            field_name: field_value
            for field_name, field_value in values.items()
            if field_name not in copy_vals
        }
        version_fields = self.env['hr.version']._fields
        copy_vals = {
            k: v
            for k, v in version_to_copy.sudo().copy_data()[0].items()
            if not (k in new_version_vals and version_fields[k].type in ['one2many', 'many2many'])
        } | copy_vals
        new_version = self.env['hr.version'].sudo().create(copy_vals).sudo(False)
        with self.env.protecting([f for f_name, f in version_fields.items() if f_name not in new_version_vals and f.copy], new_version):
            properties_fields_vals = {
                field_name: field_value
                for field_name, field_value in copy_vals.items()
                if version_fields[field_name].type == 'properties' and field_name not in new_version_vals
            }
            if properties_fields_vals:  # make sure properties vals are correctly copied.
                new_version.sudo().write(properties_fields_vals)
            new_version.write(new_version_vals)
        return new_version