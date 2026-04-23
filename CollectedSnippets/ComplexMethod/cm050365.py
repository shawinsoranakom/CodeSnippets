def read_converted(self):
        field_names = self._get_sale_order_fields()
        results = []
        for sale_line in self:
            if sale_line.product_type or (sale_line.is_downpayment and sale_line.price_unit != 0):
                product_uom = sale_line.product_id.uom_id
                sale_line_uom = sale_line.product_uom_id
                item = sale_line.read(field_names, load=False)[0]
                if sale_line.product_id.tracking != 'none':
                    move_lines = sale_line.move_ids.move_line_ids.filtered(lambda ml: ml.product_id.id == sale_line.product_id.id)
                    item['lot_names'] = move_lines.lot_id.mapped('name')
                    lot_qty_by_name = {}
                    for line in move_lines:
                        lot_qty_by_name[line.lot_id.name] = lot_qty_by_name.get(line.lot_id.name, 0.0) + line.quantity
                    item['lot_qty_by_name'] = lot_qty_by_name
                if product_uom == sale_line_uom:
                    results.append(item)
                    continue
                item['product_uom_qty'] = self._convert_qty(sale_line, item['product_uom_qty'], 's2p')
                item['qty_delivered'] = self._convert_qty(sale_line, item['qty_delivered'], 's2p')
                item['qty_invoiced'] = self._convert_qty(sale_line, item['qty_invoiced'], 's2p')
                item['qty_to_invoice'] = self._convert_qty(sale_line, item['qty_to_invoice'], 's2p')
                item['price_unit'] = sale_line_uom._compute_price(item['price_unit'], product_uom)
                results.append(item)

            elif sale_line.display_type == 'line_note':
                if results:
                    if results[-1].get('customer_note'):
                        results[-1]['customer_note'] += "--" + sale_line.name
                    else:
                        results[-1]['customer_note'] = sale_line.name


        return results