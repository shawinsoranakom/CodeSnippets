def convert_to_column_insert(self, value, record, values=None, validate=True):
        # retrieve currency from values or record
        currency_field_name = self.get_currency_field(record)
        currency_field = record._fields[currency_field_name]
        if values and currency_field_name in values:
            dummy = record.new({currency_field_name: values[currency_field_name]})
            currency = dummy[currency_field_name]
        elif values and currency_field.related and currency_field.related.split('.')[0] in values:
            related_field_name = currency_field.related.split('.')[0]
            dummy = record.new({related_field_name: values[related_field_name]})
            currency = dummy[currency_field_name]
        else:
            # Note: this is wrong if 'record' is several records with different
            # currencies, which is functional nonsense and should not happen
            # BEWARE: do not prefetch other fields, because 'value' may be in
            # cache, and would be overridden by the value read from database!
            currency = record[:1].sudo().with_context(prefetch_fields=False)[currency_field_name]
            currency = currency.with_env(record.env)

        value = float(value or 0.0)
        if currency:
            return float_repr(currency.round(value), currency.decimal_places)
        return value