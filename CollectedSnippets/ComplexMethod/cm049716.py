def assign_geo_localize(self, latitude=False, longitude=False):
        if latitude and longitude:
            self.write({
                'partner_latitude': latitude,
                'partner_longitude': longitude
            })
            return True
        # Don't pass context to browse()! We need country name in english below
        for lead in self:
            if lead.partner_latitude and lead.partner_longitude:
                continue
            if lead.country_id:
                result = self.env['res.partner']._geo_localize(
                    lead.street, lead.zip, lead.city,
                    lead.state_id.name, lead.country_id.name
                )
                if result:
                    lead.write({
                        'partner_latitude': result[0],
                        'partner_longitude': result[1]
                    })
        return True