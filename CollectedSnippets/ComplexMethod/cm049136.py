def create(self, vals_list):
        for values in vals_list:
            if values.get('display_type', self.default_get(['display_type'])['display_type']):
                values.update(product_id=False, price_unit=0, product_uom_qty=0, product_uom_id=False, date_planned=False)
            else:
                values.update(self._prepare_add_missing_fields(values))
            if values.get('price_unit') and not values.get('technical_price_unit'):
                values['technical_price_unit'] = values['price_unit']

        lines = super().create(vals_list)
        for line in lines:
            if line.product_id and line.order_id.state == 'purchase':
                msg = _("Extra line with %s ", line.product_id.display_name)
                line.order_id.message_post(body=msg)
        return lines