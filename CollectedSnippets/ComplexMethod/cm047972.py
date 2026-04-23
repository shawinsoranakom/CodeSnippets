def _get_trigger_specific_field(self):
        self.ensure_one()
        match self.trigger:
            case 'on_create_or_write':
                return _get_domain_fields(self.env, self.model_id.model, self.filter_domain)
            case 'on_stage_set':
                domain = [('ttype', '=', 'many2one'), ('name', 'in', ['stage_id', 'x_studio_stage_id'])]
            case 'on_tag_set':
                domain = [('ttype', '=', 'many2many'), ('name', 'in', ['tag_ids', 'x_studio_tag_ids'])]
            case 'on_priority_set':
                domain = [('ttype', '=', 'selection'), ('name', 'in', ['priority', 'x_studio_priority'])]
            case 'on_state_set':
                domain = [('ttype', '=', 'selection'), ('name', 'in', ['state', 'x_studio_state'])]
            case 'on_user_set':
                domain = [
                    ('relation', '=', 'res.users'),
                    ('ttype', 'in', ['many2one', 'many2many']),
                    ('name', 'in', ['user_id', 'user_ids', 'x_studio_user_id', 'x_studio_user_ids']),
                ]
            case 'on_archive' | 'on_unarchive':
                domain = [('ttype', '=', 'boolean'), ('name', 'in', ['active', 'x_active'])]
            case 'on_time_created':
                domain = [('ttype', '=', 'datetime'), ('name', '=', 'create_date')]
            case 'on_time_updated':
                domain = [('ttype', '=', 'datetime'), ('name', '=', 'write_date')]
            case _:
                return self.env['ir.model.fields']
        domain += [('model_id', '=', self.model_id.id)]
        return self.env['ir.model.fields'].search(domain, limit=1)