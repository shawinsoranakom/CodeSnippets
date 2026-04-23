def create(self, vals_list):
        # format numbers: prefetch side records, then try to format according to country
        all_partner_ids = set(values['partner_id'] for values in vals_list if values.get('partner_id'))
        all_event_ids = set(values['event_id'] for values in vals_list if values.get('event_id'))
        for values in vals_list:
            if not values.get('phone'):
                continue

            related_country = self.env['res.country']
            if values.get('partner_id'):
                related_country = self.env['res.partner'].with_prefetch(all_partner_ids).browse(values['partner_id']).country_id
            if not related_country and values.get('event_id'):
                related_country = self.env['event.event'].with_prefetch(all_event_ids).browse(values['event_id']).country_id
            if not related_country:
                related_country = self.env.company.country_id
            values['phone'] = self._phone_format(number=values['phone'], country=related_country) or values['phone']

        registrations = super().create(vals_list)
        registrations._update_mail_schedulers()
        return registrations