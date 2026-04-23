def _compute_time_cycle(self):
        manual_ops = self.filtered(lambda operation: operation.time_mode == 'manual')
        for operation in manual_ops:
            operation.time_cycle = operation.time_cycle_manual
        for operation in self - manual_ops:
            data = self.env['mrp.workorder'].search([
                ('operation_id', 'in', operation.ids),
                ('qty_produced', '>', 0),
                ('state', '=', 'done')],
                limit=operation.time_mode_batch,
                order="date_finished desc, id desc")
            # To compute the time_cycle, we can take the total duration of previous operations
            # but for the quantity, we will take in consideration the qty_produced like if the capacity was 1.
            # So producing 50 in 00:10 with capacity 2, for the time_cycle, we assume it is 25 in 00:10
            # When recomputing the expected duration, the capacity is used again to divide the qty to produce
            # so that if we need 50 with capacity 2, it will compute the expected of 25 which is 00:10
            total_duration = 0  # Can be 0 since it's not an invalid duration for BoM
            cycle_number = 0  # Never 0 unless infinite item['workcenter_id'].capacity
            for item in data:
                total_duration += item['duration']
                (capacity, _setup, _cleanup) = item['workcenter_id']._get_capacity(item.product_id, item.product_uom_id, operation.bom_id.product_qty or 1)
                cycle_number += float_round((item['qty_produced'] / capacity), precision_digits=0, rounding_method='UP')
            if cycle_number:
                operation.time_cycle = total_duration / cycle_number
            else:
                operation.time_cycle = operation.time_cycle_manual

        for operation in self:
            workcenter = self.env.context.get('workcenter', operation.workcenter_id)
            product = (
                self.env.context.get('product', operation.bom_id.product_id)
                or self.env.context.get(
                    'action_button_product',
                    operation.bom_id.product_tmpl_id.product_variant_ids.filtered(
                        lambda p: p.product_template_attribute_value_ids <= operation.bom_product_template_attribute_value_ids,
                    ),
                )
            )
            if len(product) > 1:
                product = product[0]
            quantity = self.env.context.get('quantity', operation.bom_id.product_qty or 1)
            unit = self.env.context.get('unit', operation.bom_id.product_uom_id)
            (capacity, setup, cleanup) = workcenter._get_capacity(product, unit, operation.bom_id.product_qty or 1)
            operation.cycle_number = float_round(quantity / capacity, precision_digits=0, rounding_method="UP")
            operation.time_total = setup + cleanup + operation.cycle_number * operation.time_cycle * 100.0 / (workcenter.time_efficiency or 100.0)
            operation.show_time_total = operation.cycle_number > 1 or not float_is_zero(setup + cleanup, precision_digits=0)