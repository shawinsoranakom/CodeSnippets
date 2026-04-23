def attributes(self, record, field_name, options, values=None):
        attrs = super().attributes(record, field_name, options, values)
        field = record._fields[field_name]

        placeholder = options.get('placeholder') or getattr(field, 'placeholder', None)
        if placeholder:
            attrs['placeholder'] = placeholder

        if options['translate'] and field.type in ('char', 'text'):
            lang = record.env.lang or 'en_US'
            base_lang = record._get_base_lang()
            if lang == base_lang:
                attrs['data-oe-translation-state'] = 'translated'
            else:
                base_value = record.with_context(lang=base_lang)[field_name]
                value = record[field_name]
                attrs['data-oe-translation-state'] = 'translated' if base_value != value else 'to_translate'

        return attrs