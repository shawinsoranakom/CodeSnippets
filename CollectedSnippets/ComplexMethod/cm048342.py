def default_get(self, fields):
        result = super().default_get(fields)

        active_model = self.env.context.get('active_model')
        if active_model != 'crm.lead':
            raise UserError(_('You can only apply this action from a lead.'))

        lead = False
        if result.get('lead_id'):
            lead = self.env['crm.lead'].browse(result['lead_id'])
        elif 'lead_id' in fields and self.env.context.get('active_id'):
            lead = self.env['crm.lead'].browse(self.env.context['active_id'])
        if lead:
            result['lead_id'] = lead.id
            partner_id = result.get('partner_id') or lead._find_matching_partner().id
            if 'action' in fields and not result.get('action'):
                result['action'] = 'exist' if partner_id else 'create'
            if 'partner_id' in fields and not result.get('partner_id'):
                result['partner_id'] = partner_id

        return result