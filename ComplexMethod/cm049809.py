def _notify_security_setting_update_prepare_values(self, content, **kwargs):
        """"Prepare rendering values for the 'mail.account_security_alert' qweb template."""
        reset_password_enabled = str2bool(self.env['ir.config_parameter'].sudo().get_param("auth_signup.reset_password", True))

        values = {
            'browser': False,
            'content': content,
            'event_datetime': fields.Datetime.now(),
            'ip_address': False,
            'location_address': False,
            'suggest_password_reset': kwargs.get('suggest_password_reset', True) and reset_password_enabled,
            'user': self,
            'useros': False,
        }
        if not request:
            return values

        city = request.geoip.get('city') or False
        region = request.geoip.get('region_name') or False
        country = request.geoip.get('country') or False
        if country:
            if region and city:
                values['location_address'] = _("Near %(city)s, %(region)s, %(country)s", city=city, region=region, country=country)
            elif region:
                values['location_address'] = _("Near %(region)s, %(country)s", region=region, country=country)
            else:
                values['location_address'] = _("In %(country)s", country=country)
        values['ip_address'] = request.httprequest.environ['REMOTE_ADDR']
        if request.httprequest.user_agent:
            if request.httprequest.user_agent.browser:
                values['browser'] = request.httprequest.user_agent.browser.capitalize()
            if request.httprequest.user_agent.platform:
                values['useros'] = request.httprequest.user_agent.platform.capitalize()
        return values