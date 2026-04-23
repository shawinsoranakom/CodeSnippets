def _import_ubl_invoice_line_get_product_base_line_kwargs(self, collected_values):
        to_write = collected_values['to_write']

        taxes = self.env['account.tax']
        for tax_values in collected_values['taxes_values']:
            if tax := tax_values.get('tax'):
                taxes |= tax

        base_line_kwargs = {
            **self._import_ubl_invoice_get_default_base_line_kwargs(collected_values),
            'quantity': to_write['quantity'],
            'price_unit': to_write['price_unit'],
            'discount': to_write['discount'],
            'tax_ids': taxes,
        }
        if product := collected_values['product_values'].get('product'):
            base_line_kwargs['product_id'] = product
        if uom := collected_values['product_uom_values'].get('uom'):
            base_line_kwargs['product_uom_id'] = uom
        if account := collected_values['account_values'].get('account'):
            base_line_kwargs['account_id'] = account

        if name := collected_values.get('name'):
            base_line_kwargs['_create_values']['name'] = name
        if deferred_start_date := to_write.get('deferred_start_date'):
            base_line_kwargs['_create_values']['deferred_start_date'] = deferred_start_date
        if deferred_end_date := to_write.get('deferred_end_date'):
            base_line_kwargs['_create_values']['deferred_end_date'] = deferred_end_date
        return base_line_kwargs