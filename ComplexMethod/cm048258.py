def write(self, vals):
        res = super(ResPartner, self).write(vals)

        if 'iap_enrich_info' in vals or 'iap_search_domain' in vals:
            # Not done with inverse method so we do need to search
            # for existing <res.partner.iap> only once
            partner_iaps = self.env['res.partner.iap'].sudo().search([('partner_id', 'in', self.ids)])
            missing_partners = self
            for partner_iap in partner_iaps:
                if 'iap_enrich_info' in vals:
                    partner_iap.iap_enrich_info = vals['iap_enrich_info']
                if 'iap_search_domain' in vals:
                    partner_iap.iap_search_domain = vals['iap_search_domain']

                missing_partners -= partner_iap.partner_id

            if missing_partners:
                # Create new <res.partner.iap> for missing records
                self.env['res.partner.iap'].sudo().create([
                    {
                        'partner_id': partner.id,
                        'iap_enrich_info': vals.get('iap_enrich_info'),
                        'iap_search_domain': vals.get('iap_search_domain'),
                    } for partner in missing_partners
                ])
        return res