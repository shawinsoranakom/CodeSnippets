def _translate_google_to_standard(self, google_fields):
        standard_data = {}

        for google_field in google_fields:
            fields_standard = FIELDS_MAPPING.get(google_field['type'], [])

            for field_standard in fields_standard:
                if field_standard in standard_data:  # if a value is already assigned, do not overwrite it.
                    continue
                if field_standard == 'country':
                    country = request.env['res.country'].search([('code', '=', google_field['short_name'].upper())], limit=1)
                    standard_data[field_standard] = [country.id, country.name]
                elif field_standard == 'state':
                    if 'country' not in standard_data:
                        _logger.warning(
                            "Cannot assign state before country:\n%s", pformat(google_fields),
                        )
                        continue
                    state = request.env['res.country.state'].search(
                        [
                            ('country_id', '=', standard_data['country'][0]),
                            '|',
                            ('code', '=', google_field['short_name'].upper()),
                            ('name', 'ilike', google_field['long_name']),
                        ],
                    )
                    if len(state) == 1:
                        standard_data[field_standard] = [state.id, state.name]
                else:
                    standard_data[field_standard] = google_field['long_name']
        city_name = standard_data.get('city')
        country = standard_data.get('country')
        country_id = country[0] if country else False
        if city := self.env['res.partner']._get_res_city_by_name(city_name, country_id):
            standard_data['city_id'] = [city.id, city.name]
            if not standard_data.get('state') and city.state_id:  # Derive state from city if missing
                standard_data['state'] = [city.state_id.id, city.state_id.name]
        return standard_data