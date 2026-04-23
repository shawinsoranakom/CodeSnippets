def copy_data(self, default=None):
        default = dict(default or {}, config_ids=[(5, 0, 0)])
        vals_list = super().copy_data(default=default)

        for pm, vals in zip(self, vals_list):
            if pm.journal_id and pm.journal_id.type == 'cash':
                if ('journal_id' in default and default['journal_id'] == pm.journal_id.id) or ('journal_id' not in default):
                    vals['journal_id'] = False
        return vals_list