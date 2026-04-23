def _compute_cumulative_fields(self):
        total_records_grouped = self.env['stock.avco.report'].search(
            [('product_id', 'in', self.product_id.mapped('id')), ('company_id', 'in', self.company_id.mapped('id'))]
        ).grouped(lambda m: (m.product_id, m.company_id))
        for records in self.grouped(lambda m: (m.product_id, m.company_id)).values():
            current_page_records = records.sorted('date, id')
            total_records = total_records_grouped.get((records.product_id, records.company_id)).sorted('date, id')
            added_value = 0.0
            total_value = 0.0
            total_quantity = 0.0
            avco = 0.0
            for record in total_records:
                qty = record.quantity
                if record.res_model_name == 'stock.move':
                    previous_qty = total_quantity
                    total_quantity += qty
                    if qty > 0:
                        added_value = record.value
                        # Regular case, value from accumulation
                        if previous_qty > 0:
                            total_value += added_value
                            avco = total_value / total_quantity if not float_is_zero(total_quantity, precision_digits=self.env['decimal.precision'].precision_get('Product Unit')) else avco
                        # From negative quantity case, value from last_in
                        elif previous_qty <= 0:
                            avco = added_value / qty if qty else avco
                            total_value = avco * total_quantity
                    else:
                        added_value = avco * qty
                        total_value += added_value

                elif record.res_model_name == 'product.value':
                    avco = record.value
                    added_value = (avco * total_quantity) - total_value
                    total_value = avco * total_quantity

                if record in current_page_records:
                    record.added_value = added_value
                    record.total_value = total_value
                    record.total_quantity = total_quantity
                    record.avco_value = avco