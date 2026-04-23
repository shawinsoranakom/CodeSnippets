def default_get(self, fields):
        res = super().default_get(fields)

        if not res.get('src_list_ids') and 'src_list_ids' in fields:
            if self.env.context.get('active_model') != 'mailing.list':
                raise UserError(_('You can only apply this action from Mailing Lists.'))
            src_list_ids = self.env.context.get('active_ids')
            res.update({
                'src_list_ids': [(6, 0, src_list_ids)],
            })
        if not res.get('dest_list_id') and 'dest_list_id' in fields:
            src_list_ids = res.get('src_list_ids') or self.env.context.get('active_ids')
            res.update({
                'dest_list_id': src_list_ids and src_list_ids[0] or False,
            })
        return res