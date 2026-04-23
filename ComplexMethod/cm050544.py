def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        copy_from_template = self.env.context.get('copy_from_template')
        for project, vals in zip(self, vals_list):
            if project.is_template and not copy_from_template:
                vals['is_template'] = True
            if copy_from_template:
                for field in self._get_template_field_blacklist():
                    if field in vals and field not in default:
                        del vals[field]
            if copy_from_template or (not project.is_template and vals.get('is_template')):
                vals['name'] = default.get('name', project.name)
            else:
                vals['name'] = default.get('name', self.env._('%s (copy)', project.name))
        return vals_list