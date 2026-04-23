def test_related_fields_on_version(self):
        """ Some groups have been added to avoid users with basic access to HR app see some critical (like wage field for instance)
            This test makes sure the groups added in version fields is also in the employee fields related.
            However, to define the same groups in employee fields, we have to redefine the related fields (readonly=False, related='version_id.{field_name})
            Otherwise, the field we loose the linked with the version field and could be readonly instead of editable.
        """
        version_fields = {
            f_name: field
            for f_name, field in self.env['hr.version']._fields.items()
            if field.groups and field.groups not in ['hr.group_hr_user', 'base.group_user'] and not (field.related and field.related.startswith('employee_id'))
        }
        employee_fields = {
            f_name: field
            for f_name, field in self.env['hr.employee']._fields.items()
            if f_name in version_fields
        }
        fields_without_group = []
        fields_without_related = []
        fields_readonly = []
        for f_name, field in employee_fields.items():
            v_field = version_fields[f_name]
            if not (field.groups and field.groups != v_field):
                fields_without_group.append(f_name)
            elif not (field.related and field.related == f'version_id.{f_name}'):
                fields_without_related.append(f_name)
            elif field.readonly != v_field.readonly:
                fields_readonly.append(f_name)
        self.assertFalse(fields_without_group, "Inconsistency between some employee fields and version ones (those employees fields should have the same groups than related one in version")
        self.assertFalse(fields_without_related, "Some employee fields have the same name than the version ones but they are not related")
        self.assertFalse(fields_readonly, "(Readonly) Inconsistency between some employee fields and version ones, the both fields (in version and employee) have to be readonly or editable")