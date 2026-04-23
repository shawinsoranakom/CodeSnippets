def _send_totp_mail_code(self):
        self.ensure_one()
        self._totp_rate_limit('send_email')

        if not self.email:
            raise UserError(_("Cannot send email: user %s has no email address.", self.name))

        template = self.env.ref('auth_totp_mail.mail_template_totp_mail_code').sudo()
        context = {}
        if request:
            device = request.httprequest.user_agent.platform
            browser = request.httprequest.user_agent.browser
            context.update({
                'location': None,
                'device': device and device.capitalize() or None,
                'browser': browser and browser.capitalize() or None,
                'ip': request.httprequest.environ['REMOTE_ADDR'],
            })
            if request.geoip.city.name:
                context['location'] = f"{request.geoip.city.name}, {request.geoip.country_name}"

        email_values = {
            'email_to': self.email,
            'email_cc': False,
            'auto_delete': True,
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
        }
        template.with_context(**context).send_mail(
            self.id, force_send=True, raise_exception=True,
            email_values=email_values,
            email_layout_xmlid='mail.mail_notification_light'
        )