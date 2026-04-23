def search_geo_partner(self):
        Partner = self.env['res.partner']
        res_partner_ids = {}
        self.assign_geo_localize()
        for lead in self:
            partner_ids = []
            if not lead.country_id:
                continue
            latitude = lead.partner_latitude
            longitude = lead.partner_longitude
            if latitude and longitude:
                # 1. first way: in the same country, small area
                partner_ids = Partner.search([
                    ('partner_weight', '>', 0),
                    ('partner_latitude', '>', latitude - 2), ('partner_latitude', '<', latitude + 2),
                    ('partner_longitude', '>', longitude - 1.5), ('partner_longitude', '<', longitude + 1.5),
                    ('country_id', '=', lead.country_id.id),
                    ('id', 'not in', lead.partner_declined_ids.ids),
                ])

                # 2. second way: in the same country, big area
                if not partner_ids:
                    partner_ids = Partner.search([
                        ('partner_weight', '>', 0),
                        ('partner_latitude', '>', latitude - 4), ('partner_latitude', '<', latitude + 4),
                        ('partner_longitude', '>', longitude - 3), ('partner_longitude', '<', longitude + 3),
                        ('country_id', '=', lead.country_id.id),
                        ('id', 'not in', lead.partner_declined_ids.ids),
                    ])

                # 3. third way: in the same country, extra large area
                if not partner_ids:
                    partner_ids = Partner.search([
                        ('partner_weight', '>', 0),
                        ('partner_latitude', '>', latitude - 8), ('partner_latitude', '<', latitude + 8),
                        ('partner_longitude', '>', longitude - 8), ('partner_longitude', '<', longitude + 8),
                        ('country_id', '=', lead.country_id.id),
                        ('id', 'not in', lead.partner_declined_ids.ids),
                    ])

                # 5. fifth way: anywhere in same country
                if not partner_ids:
                    # still haven't found any, let's take all partners in the country!
                    partner_ids = Partner.search([
                        ('partner_weight', '>', 0),
                        ('country_id', '=', lead.country_id.id),
                        ('id', 'not in', lead.partner_declined_ids.ids),
                    ])

                # 6. sixth way: closest partner whatsoever, just to have at least one result
                if not partner_ids:
                    # warning: point() type takes (longitude, latitude) as parameters in this order!
                    self.env.cr.execute("""SELECT id, distance
                                  FROM  (select id, (point(partner_longitude, partner_latitude) <-> point(%s,%s)) AS distance FROM res_partner
                                  WHERE active
                                        AND partner_longitude is not null
                                        AND partner_latitude is not null
                                        AND partner_weight > 0
                                        AND id not in (select partner_id from crm_lead_declined_partner where lead_id = %s)
                                        ) AS d
                                  ORDER BY distance LIMIT 1""", (longitude, latitude, lead.id))
                    res = self.env.cr.dictfetchone()
                    if res:
                        partner_ids = Partner.browse([res['id']])

                if partner_ids:
                    res_partner_ids[lead.id] = random.choices(
                        partner_ids.ids,
                        partner_ids.mapped('partner_weight'),
                    )[0]

        return res_partner_ids