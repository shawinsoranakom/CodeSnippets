def action_forward(self):
        self.ensure_one()
        template = self.env.ref('website_crm_partner_assign.email_template_lead_forward_mail', False)
        if not template:
            raise UserError(_('The Forward Email Template is not in the database'))
        portal_group = self.env.ref('base.group_portal')

        local_context = self.env.context.copy()
        if not (self.forward_type == 'single'):
            no_email = set()
            for lead in self.assignation_lines:
                if lead.partner_assigned_id and not lead.partner_assigned_id.email:
                    no_email.add(lead.partner_assigned_id.name)
            if no_email:
                raise UserError(_('Set an email address for the partner(s): %s', ", ".join(no_email)))
        if self.forward_type == 'single' and not self.partner_id.email:
            raise UserError(_('Set an email address for the partner %s', self.partner_id.name))

        partners_leads = {}
        for lead in self.assignation_lines:
            partner = self.forward_type == 'single' and self.partner_id or lead.partner_assigned_id
            lead_details = {
                'lead_link': lead.lead_link,
                'lead_id': lead.lead_id,
            }
            if partner:
                partner_leads = partners_leads.get(partner.id)
                if partner_leads:
                    partner_leads['leads'].append(lead_details)
                else:
                    partners_leads[partner.id] = {'partner': partner, 'leads': [lead_details]}

        for partner_id, partner_leads in partners_leads.items():
            in_portal = False
            if portal_group:
                for contact in (partner.child_ids or partner).filtered(lambda contact: contact.user_ids):
                    in_portal = portal_group.id in [g.id for g in contact.user_ids[0].all_group_ids]

            local_context['partner_id'] = partner_leads['partner']
            local_context['partner_leads'] = partner_leads['leads']
            local_context['partner_in_portal'] = in_portal
            template.with_context(local_context).send_mail(self.id)
            leads = self.env['crm.lead']
            for lead_data in partner_leads['leads']:
                leads |= lead_data['lead_id']
            values = {'partner_assigned_id': partner_id, 'user_id': partner_leads['partner'].user_id.id}
            leads.with_context(mail_auto_subscribe_no_notify=1).write(values)
            # TDE FIXME: check for assigned in suggested recipients (master-)
            self.env['crm.lead'].message_subscribe([partner_id])
        return True