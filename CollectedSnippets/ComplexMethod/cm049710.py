def _convert_to_assignation_line(self, lead, partner):
        lead_location = []
        partner_location = []
        if lead.country_id:
            lead_location.append(lead.country_id.name)
        if lead.city:
            lead_location.append(lead.city)
        if partner:
            if partner.country_id:
                partner_location.append(partner.country_id.name)
            if partner.city:
                partner_location.append(partner.city)
        return {'lead_id': lead.id,
                'lead_location': ", ".join(lead_location),
                'partner_assigned_id': partner and partner.id or False,
                'partner_location': ", ".join(partner_location),
                'lead_link': self.get_lead_portal_url(lead),
                }