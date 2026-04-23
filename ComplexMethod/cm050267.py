def _prepare_create_values(self, vals_list):
        result = super()._prepare_create_values(vals_list)
        new_vals_list = []
        Version = self.env['hr.version']
        version_fields = [fname for fname, field in Version._fields.items() if Version._has_field_access(field, 'write')]
        for vals in result:
            employee_vals = {}
            version_vals = {}
            for fname, value in vals.items():
                employee_field = self._fields.get(fname)
                if not (employee_field and employee_field.inherited and employee_field.related_field.model_name == 'hr.version'):
                    employee_vals[fname] = value
                else:
                    version_vals[fname] = value
            new_vals_list.append({
                **employee_vals,
                **{k: v for k, v in version_vals.items() if k in version_fields},
            })
        return new_vals_list