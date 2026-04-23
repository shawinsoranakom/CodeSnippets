def record_to_html(self, record, field_name, options):
        options = dict(options)
        #currency should be specified by monetary field
        field = record._fields[field_name]

        if not options.get('display_currency') and field.type == 'monetary' and field.get_currency_field(record):
            options['display_currency'] = record[field.get_currency_field(record)]
        if not options.get('display_currency'):
            # search on the model if they are a res.currency field to set as default
            fields = record._fields.items()
            currency_fields = [k for k, v in fields if v.type == 'many2one' and v.comodel_name == 'res.currency']
            if currency_fields:
                options['display_currency'] = record[currency_fields[0]]
        if 'date' not in options:
            options['date'] = record.env.context.get('date')
        if 'company_id' not in options:
            options['company_id'] = record.env.context.get('company_id')

        return super().record_to_html(record, field_name, options)