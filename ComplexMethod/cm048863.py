def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values, po):
        line_description = ''
        if values.get('product_description_variants'):
            line_description = values['product_description_variants']
        supplier = values.get('supplier')
        if not values.get('force_uom') and supplier.product_uom_id != product_uom:
            product_qty = product_uom._compute_quantity(product_qty, supplier.product_uom_id)
            product_uom = supplier.product_uom_id
        res = self.with_context(procurement_values=values)._prepare_purchase_order_line(product_id, product_qty, product_uom, company_id, supplier.partner_id, po)
        # We need to keep the vendor name set in _prepare_purchase_order_line. To avoid redundancy
        # in the line name, we add the line_description only if different from the product name.
        # This way, we shoud not lose any valuable information.
        if line_description and product_id.name != line_description:
            res['name'] = (res['name'] + '\n' + line_description).strip()
        res['date_planned'] = fields.Datetime.to_datetime(values.get('date_planned'))
        # The date must be day before or equal at the supplier target day
        if po.partner_id.group_rfq == 'week' and po.partner_id.group_on != 'default':
            delta_days = (7 + int(po.partner_id.group_on) - res['date_planned'].isoweekday()) % 7
            res['date_planned'] = res['date_planned'] + relativedelta(days=delta_days)
            if not po.date_planned or po.date_planned >= res['date_planned']:
                # date_order was computed based on procurement date_planned. If the PO date_planned is
                # shifted, we also need to shift the date_order.
                po.date_order = fields.Datetime.to_datetime(po.date_order) + relativedelta(days=delta_days)
        res['move_dest_ids'] = [(4, x.id) for x in values.get('move_dest_ids', [])]
        res['location_final_id'] = location_dest_id.id
        res['orderpoint_id'] = values.get('orderpoint_id', False) and values.get('orderpoint_id').id
        res['propagate_cancel'] = values.get('propagate_cancel')
        res['product_description_variants'] = values.get('product_description_variants')
        res['product_no_variant_attribute_value_ids'] = values.get('never_product_template_attribute_value_ids')
        return res