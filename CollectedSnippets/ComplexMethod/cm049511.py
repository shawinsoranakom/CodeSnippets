def write(self, vals):
        result = super().write(vals)
        if self.env.context.get('salary_simulation'):
            return result
        if vals.get('contract_date_end') or vals.get('contract_date_start') or vals.get('date_version'):
            self.sudo()._remove_work_entries()
        dependent_fields = self._get_fields_that_recompute_we()
        if any(key in dependent_fields for key in vals):
            for version_sudo in self.sudo():
                date_from = max(version_sudo.date_start, version_sudo.date_generated_from.date())
                date_to = min(version_sudo.date_end or date.max, version_sudo.date_generated_to.date())
                if date_from != date_to and self.employee_id:
                    version_sudo._recompute_work_entries(date_from, date_to)
        return result