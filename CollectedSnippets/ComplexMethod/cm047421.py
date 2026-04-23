def set_values(self):
        """
        Set values for the fields other that `default`, `group` and `module`
        """
        self = self.with_context(active_test=False)
        classified = self._get_classified_fields()
        current_settings = self.default_get(list(self.fields_get()))

        # default values fields
        IrDefault = self.env['ir.default'].sudo()
        for name, model, field in classified['default']:
            if isinstance(self[name], models.BaseModel):
                if self._fields[name].type == 'many2one':
                    value = self[name].id
                else:
                    value = self[name].ids
            else:
                value = self[name]
            if name not in current_settings or value != current_settings[name]:
                IrDefault.set(model, field, value)

        # group fields: modify group / implied groups
        for name, groups, implied_group in sorted(classified['group'], key=lambda k: self[k[0]]):
            groups = groups.sudo()
            implied_group = implied_group.sudo()
            if self[name] == current_settings[name]:
                continue
            if int(self[name]):
                groups._apply_group(implied_group)
            else:
                groups._remove_group(implied_group)

        # config fields: store ir.config_parameters
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        for name, icp in classified['config']:
            field = self._fields[name]
            value = self[name]
            current_value = IrConfigParameter.get_param(icp)

            if field.type == 'char':
                # storing developer keys as ir.config_parameter may lead to nasty
                # bugs when users leave spaces around them
                value = (value or "").strip() or False
            elif field.type in ('integer', 'float'):
                value = repr(value) if value else False
            elif field.type == 'many2one':
                # value is a (possibly empty) recordset
                value = value.id

            if current_value == str(value) or current_value == value:
                continue
            IrConfigParameter.set_param(icp, value)