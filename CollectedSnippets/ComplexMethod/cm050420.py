def create(self, vals_list):
        for vals in vals_list:
            if vals.get('website'):
                vals['website'] = self.env['res.partner']._clean_website(vals['website'])
        leads = super().create(vals_list)

        # handling a date_closed value if the lead is directly created in the won stage
        won_to_set = leads.filtered(lambda l: not l.date_closed and l.stage_id.is_won)
        won_to_set.write({'date_closed': fields.Datetime.now()})

        if self.default_get(['partner_id']).get('partner_id') is None:
            commercial_partner_ids = [vals['commercial_partner_id'] for vals in vals_list if vals.get('commercial_partner_id')]
            CommercialPartners = self.env['res.partner'].with_prefetch(commercial_partner_ids)
            for lead, lead_vals in zip(leads, vals_list, strict=True):
                if not lead_vals.get('partner_id') and lead_vals.get('commercial_partner_id'):
                    commercial_partner = CommercialPartners.browse(lead_vals['commercial_partner_id'])
                    if (lead.phone or lead.email_from) and (
                        lead.phone_sanitized != commercial_partner.phone_sanitized or
                        lead.email_normalized != commercial_partner.email_normalized
                    ):
                        lead.partner_name = lead.partner_name or commercial_partner.name
                        continue
                    lead.partner_id = commercial_partner

        leads._handle_won_lost({}, {
            lead.id: {
                'is_lost': lead.won_status == 'lost',
                'is_won': lead.won_status == 'won',
            } for lead in leads
        })

        return leads