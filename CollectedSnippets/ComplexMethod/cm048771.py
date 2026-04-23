def _get_base_line_field_value_from_record(self, record, field, extra_values, fallback, from_base_line=False):
        """ Helper to extract a default value for a record or something looking like a record.

        Suppose field is 'product_id' and fallback is 'self.env['product.product']'

        if record is an account.move.line, the returned product_id will be `record.product_id._origin`.
        if record is a dict, the returned product_id will be `record.get('product_id', fallback)`.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param record:          A record or a dict or a falsy value.
        :param field:           The name of the field to extract.
        :param extra_values:    The extra kwargs passed in addition of 'record'.
        :param fallback:        The value to return if not found in record or extra_values.
        :param from_base_line:  Indicate if the value has to be retrieved automatically from the base_line and not the record.
                                False by default.
        :return:                The field value corresponding to 'field'.
        """
        need_origin = isinstance(fallback, models.Model)
        if field in extra_values:
            value = extra_values[field] or fallback
        elif isinstance(record, models.Model) and field in record._fields and not from_base_line:
            value = record[field]
        elif isinstance(record, dict):
            value = record.get(field, fallback)
        else:
            value = fallback
        if need_origin:
            value = value._origin
        return value