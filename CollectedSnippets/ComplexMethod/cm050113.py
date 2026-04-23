def _compute_medium_id(self):
        super()._compute_medium_id()
        for mailing in self:
            if mailing.mailing_type == 'sms' and (not mailing.medium_id or mailing.medium_id == self.env['utm.medium']._fetch_or_create_utm_medium('email')):
                mailing.medium_id = self.env['utm.medium']._fetch_or_create_utm_medium("sms", module="mass_mailing_sms").id
            elif mailing.mailing_type == 'mail' and (not mailing.medium_id or mailing.medium_id == self.env['utm.medium']._fetch_or_create_utm_medium("sms", module="mass_mailing_sms")):
                mailing.medium_id = self.env['utm.medium']._fetch_or_create_utm_medium('email').id