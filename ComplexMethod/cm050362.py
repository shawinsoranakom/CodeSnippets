def get_tender_best_lines(self):
        product_to_best_price_line = defaultdict(lambda: self.env['purchase.order.line'])
        product_to_best_date_line = defaultdict(lambda: self.env['purchase.order.line'])
        product_to_best_price_unit = defaultdict(lambda: self.env['purchase.order.line'])
        po_alternatives = self | self.alternative_po_ids

        for line in po_alternatives.order_line:
            if not line.product_qty or not line.price_total_cc or line.state in ['cancel', 'purchase']:
                continue

            # if no best price line => no best price unit line either
            if not product_to_best_price_line[line.product_id]:
                product_to_best_price_line[line.product_id] = line
                product_to_best_price_unit[line.product_id] = line
            else:
                price_subtotal = line.price_total_cc
                price_unit = line.price_total_cc / line.product_qty
                current_price_subtotal = product_to_best_price_line[line.product_id][0].price_total_cc
                current_price_unit = product_to_best_price_unit[line.product_id][0].price_total_cc / product_to_best_price_unit[line.product_id][0].product_qty

                if current_price_subtotal > price_subtotal:
                    product_to_best_price_line[line.product_id] = line
                elif current_price_subtotal == price_subtotal:
                    product_to_best_price_line[line.product_id] |= line
                if current_price_unit > price_unit:
                    product_to_best_price_unit[line.product_id] = line
                elif current_price_unit == price_unit:
                    product_to_best_price_unit[line.product_id] |= line

            if not product_to_best_date_line[line.product_id] or product_to_best_date_line[line.product_id][0].date_planned > line.date_planned:
                product_to_best_date_line[line.product_id] = line
            elif product_to_best_date_line[line.product_id][0].date_planned == line.date_planned:
                product_to_best_date_line[line.product_id] |= line

        best_price_ids = set()
        best_date_ids = set()
        best_price_unit_ids = set()
        for lines in product_to_best_price_line.values():
            best_price_ids.update(lines.ids)
        for lines in product_to_best_date_line.values():
            best_date_ids.update(lines.ids)
        for lines in product_to_best_price_unit.values():
            best_price_unit_ids.update(lines.ids)
        return list(best_price_ids), list(best_date_ids), list(best_price_unit_ids)