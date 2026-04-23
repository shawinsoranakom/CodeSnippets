def _handle_website_form(self, model_name, **kwargs):
        model_record = request.env['ir.model'].sudo().search([('model', '=', model_name), ('website_form_access', '=', True)])
        if model_record:
            try:
                data = self.extract_data(model_record, request.params)
            except:
                # no specific management, super will do it
                pass
            else:
                record = data.get('record', {})
                phone_fields = request.env[model_name]._phone_get_number_fields()
                country = request.env['res.country'].browse(record.get('country_id'))
                contact_country = country if country.exists() else self._get_country()
                for phone_field in phone_fields:
                    if not record.get(phone_field):
                        continue
                    number = record[phone_field]
                    fmt_number = phone_validation.phone_format(
                        number, contact_country.code if contact_country else None,
                        contact_country.phone_code if contact_country else None,
                        force_format='INTERNATIONAL',
                        raise_exception=False
                    )
                    request.params.update({phone_field: fmt_number})

        if model_name == 'crm.lead' and not request.params.get('state_id'):
            geoip_country_code = request.geoip.country_code
            geoip_state_code = request.geoip.subdivisions[0].iso_code if request.geoip.subdivisions else None
            if geoip_country_code and geoip_state_code:
                state = request.env['res.country.state'].search([('code', '=', geoip_state_code), ('country_id.code', '=', geoip_country_code)])
                if state:
                    request.params['state_id'] = state.id
        return super(WebsiteForm, self)._handle_website_form(model_name, **kwargs)