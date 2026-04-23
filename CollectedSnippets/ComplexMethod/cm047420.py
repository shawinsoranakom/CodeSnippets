def default_get(self, fields):
        res = super().default_get(fields)
        if not fields:
            return res

        IrDefault = self.env['ir.default']
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        classified = self._get_classified_fields(fields)

        # defaults: take the corresponding default value they set
        for name, model, field in classified['default']:
            value = IrDefault._get(model, field)
            if value is not None:
                res[name] = value

        # groups: which groups are implied by the group Employee
        for name, groups, implied_group in classified['group']:
            res[name] = all(implied_group in group.all_implied_ids for group in groups)
            if self._fields[name].type == 'selection':
                res[name] = str(int(res[name]))     # True, False -> '1', '0'

        # modules: which modules are installed/to install
        for module in classified['module']:
            res[f'module_{module.name}'] = module.state in ('installed', 'to install', 'to upgrade')

        # config: get & convert stored ir.config_parameter (or default)
        WARNING_MESSAGE = "Error when converting value %r of field %s for ir.config.parameter %r"
        for name, icp in classified['config']:
            field = self._fields[name]
            value = IrConfigParameter.get_param(icp, field.default(self) if field.default else False)
            if value is not False:
                if field.type == 'many2one':
                    try:
                        # Special case when value is the id of a deleted record, we do not want to
                        # block the settings screen
                        value = self.env[field.comodel_name].browse(int(value)).exists().id
                    except (ValueError, TypeError):
                        _logger.warning(WARNING_MESSAGE, value, field, icp)
                        value = False
                elif field.type == 'integer':
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        _logger.warning(WARNING_MESSAGE, value, field, icp)
                        value = 0
                elif field.type == 'float':
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        _logger.warning(WARNING_MESSAGE, value, field, icp)
                        value = 0.0
                elif field.type == 'boolean':
                    value = str2bool(value, bool(value))
            res[name] = value

        res.update(self.get_values())

        return res