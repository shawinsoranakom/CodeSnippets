def default_get(self, fields):
        res = super(CrmLeadForwardToPartner, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        if 'body' in fields:
            template = self.env.ref('website_crm_partner_assign.email_template_lead_forward_mail', False)
            if template:
                res['body'] = template.body_html
        if active_ids:
            default_composition_mode = self.env.context.get('default_composition_mode')
            res['assignation_lines'] = []
            leads = self.env['crm.lead'].browse(active_ids)
            if default_composition_mode == 'mass_mail':
                partner_assigned_dict = leads.search_geo_partner()
            else:
                partner_assigned_dict = {lead.id: lead.partner_assigned_id.id for lead in leads}
                res['partner_id'] = leads[0].partner_assigned_id.id
            for lead in leads:
                partner_id = partner_assigned_dict.get(lead.id) or False
                partner = self.env['res.partner'].browse(partner_id)
                res['assignation_lines'].append((0, 0, self._convert_to_assignation_line(lead, partner)))
        return res