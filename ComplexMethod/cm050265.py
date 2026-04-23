def write(self, vals):
        # Employee Versions Validation
        if 'employee_id' in vals:
            if self.filtered(lambda v: v.employee_id and v.employee_id.version_ids <= self and vals['employee_id'] != v.employee_id.id):
                raise ValidationError(self.env._("Cannot unassign all the active versions of an employee."))
        if 'active' in vals and not vals['active']:
            if self.filtered(lambda v: v.employee_id and v.employee_id.version_ids <= self):
                raise ValidationError(self.env._("Cannot archive all the active versions of an employee."))

        if self.env.context.get('sync_contract_dates') or ("contract_date_start" not in vals and "contract_date_end" not in vals):
            return super().write(vals)

        for versions_by_employee in self.grouped('employee_id').values():
            if len(versions_by_employee.grouped('contract_date_start').keys()) > 1:
                raise ValidationError(self.env._("Cannot modify multiple versions contract dates with different contracts at once."))

        multiple_versions = self
        if vals.get("contract_date_start"):
            unique_versions = multiple_versions.filtered(lambda v: len(v.employee_id.version_ids) == 1)
            multiple_versions -= unique_versions
            if len(unique_versions):
                unique_versions.with_context(sync_contract_dates=True).write({
                    **vals,
                    "date_version": vals["contract_date_start"]
                })

        if not any(multiple_versions.mapped('contract_date_start')):
            return super(HrVersion, multiple_versions).write(vals)

        new_vals = {
            f_name: f_value
            for f_name, f_value in vals.items()
            if (f_name != 'contract_date_start' or not f_value) and f_name != 'contract_date_end'
        }
        for employee, versions in multiple_versions.grouped('employee_id').items():

            dates_vals = {}
            first_version = next(iter(versions), versions)

            if "contract_date_start" in vals:
                dates_vals["contract_date_start"] = fields.Date.to_date(vals.get('contract_date_start'))
            else:
                dates_vals["contract_date_start"] = first_version.contract_date_start
            if "contract_date_end" in vals:
                dates_vals["contract_date_end"] = fields.Date.to_date(vals.get('contract_date_end'))
            else:
                dates_vals["contract_date_end"] = first_version.contract_date_end

            if first_version.contract_date_start:
                versions_to_sync = employee._get_contract_versions(
                    date_start=first_version.contract_date_start,
                    date_end=first_version.contract_date_end,
                )
                all_versions_to_sync = self.env['hr.version']
                for contract_versions in versions_to_sync.values():
                    all_versions_to_sync |= next(iter(contract_versions.values()))

                if all_versions_to_sync:
                    all_versions_to_sync.with_context(sync_contract_dates=True).write(dates_vals)

            else:
                versions.with_context(sync_contract_dates=True).write(dates_vals)

        return super(HrVersion, multiple_versions).write(new_vals)