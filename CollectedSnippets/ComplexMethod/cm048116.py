def _prepare_delivery_line_vals(self, carrier, price_unit):
        context = {}
        if self.partner_id:
            # set delivery detail in the customer language
            context['lang'] = self.partner_id.lang
            carrier = carrier.with_context(lang=self.partner_id.lang)

        # Apply fiscal position
        taxes = carrier.product_id.taxes_id._filter_taxes_by_company(self.company_id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(taxes).ids

        # Create the sales order line

        if carrier.product_id.description_sale:
            so_description = '%s: %s' % (carrier.name,
                                        carrier.product_id.description_sale)
        else:
            so_description = carrier.name
        values = {
            'order_id': self.id,
            'name': so_description,
            'price_unit': price_unit,
            'product_uom_qty': 1,
            'product_id': carrier.product_id.id,
            'tax_ids': [(6, 0, taxes_ids)],
            'is_delivery': True,
        }
        if carrier.free_over and self.currency_id.is_zero(price_unit) :
            values['name'] = _('%s\nFree Shipping', values['name'])
        if self.order_line:
            values['sequence'] = self.order_line[-1].sequence + 1
        del context
        return values