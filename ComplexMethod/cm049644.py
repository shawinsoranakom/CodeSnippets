def _filter_records_to_values(self, records, **options):
        """
        Extract the fields from the data source 'records' and put them into a dictionary of values

        @param records: Model records returned by the filter
        @param options: Additional options:
        - res_model (str): The name of the targeted model.
        - is_sample (bool): True if conversion is for sample records.

        @return List of dict associating the field value to each field name
        """
        self and self.ensure_one()
        model = self.env[self.model_name or options.get('res_model')]
        meta_data = self._get_filter_meta_data(model)

        values = []
        Website = self.env['website']
        for record in records:
            data = {}
            for field_name, field_widget in meta_data.items():
                field = model._fields.get(field_name)
                if field and field.type in ('binary', 'image'):
                    if options.get('is_sample'):
                        data[field_name] = record[field_name].decode('utf8') if field_name in record else '/web/image'
                    else:
                        data[field_name] = Website.image_url(record, field_name)
                elif field_widget == 'monetary':
                    model_currency = None
                    if field and field.type == 'monetary':
                        model_currency = record[field.get_currency_field(record)]
                    elif 'currency_id' in model._fields:
                        model_currency = record['currency_id']
                    if model_currency:
                        website_currency = self._get_website_currency()
                        data[field_name] = model_currency._convert(
                            record[field_name],
                            website_currency,
                            Website.get_current_website().company_id,
                            fields.Date.today()
                        )
                    else:
                        data[field_name] = record[field_name]
                else:
                    data[field_name] = record[field_name]

            data['call_to_action_url'] = 'website_url' in record and record['website_url']
            data['_record'] = record
            values.append(data)
        return values