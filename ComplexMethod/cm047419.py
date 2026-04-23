def _get_classified_fields(self, fnames=None):
        """ return a dictionary with the fields classified by category:

            .. code-block:: python

                {   'default': [('default_foo', 'model', 'foo'), ...],
                    'group':   [('group_bar', [browse_group], browse_implied_group), ...],
                    'module':  [('module_baz', browse_module), ...],
                    'config':  [('config_qux', 'my.parameter'), ...],
                    'other':   ['other_field', ...],
                }
        """
        IrModule = self.env['ir.module.module']
        IrModelData = self.env['ir.model.data']
        Groups = self.env['res.groups']

        def ref(xml_id):
            res_model, res_id = IrModelData._xmlid_to_res_model_res_id(xml_id)
            return self.env[res_model].browse(res_id)

        if fnames is None:
            fnames = self._fields.keys()

        defaults, groups, configs, others = [], [], [], []
        modules = IrModule
        for name in fnames:
            field = self._fields[name]
            if name.startswith('default_'):
                if not hasattr(field, 'default_model'):
                    raise Exception("Field %s without attribute 'default_model'" % field)
                defaults.append((name, field.default_model, name[8:]))
            elif name.startswith('group_'):
                if field.type not in ('boolean', 'selection'):
                    raise Exception("Field %s must have type 'boolean' or 'selection'" % field)
                if not hasattr(field, 'implied_group'):
                    raise Exception("Field %s without attribute 'implied_group'" % field)
                field_group_xmlids = getattr(field, 'group', 'base.group_user').split(',')
                field_groups = Groups.concat(*(ref(it) for it in field_group_xmlids))
                groups.append((name, field_groups, ref(field.implied_group)))
            elif name.startswith('module_'):
                if field.type not in ('boolean', 'selection'):
                    raise Exception("Field %s must have type 'boolean' or 'selection'" % field)
                modules += IrModule._get(name[7:])
            elif hasattr(field, 'config_parameter') and field.config_parameter:
                if field.type not in ('boolean', 'integer', 'float', 'char', 'selection', 'many2one', 'datetime'):
                    raise Exception("Field %s must have type 'boolean', 'integer', 'float', 'char', 'selection', 'many2one' or 'datetime'" % field)
                configs.append((name, field.config_parameter))
            else:
                others.append(name)

        return {'default': defaults, 'group': groups, 'module': modules, 'config': configs, 'other': others}