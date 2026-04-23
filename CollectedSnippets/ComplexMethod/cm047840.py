def _quantity_in_progress(self):
        bom_kits = self.env['mrp.bom']._bom_find(self.product_id, bom_type='phantom')
        bom_kit_orderpoints = {
            orderpoint: bom_kits[orderpoint.product_id]
            for orderpoint in self
            if orderpoint.product_id in bom_kits
        }
        orderpoints_without_kit = self - self.env['stock.warehouse.orderpoint'].concat(*bom_kit_orderpoints.keys())
        res = super(StockWarehouseOrderpoint, orderpoints_without_kit)._quantity_in_progress()
        for orderpoint in bom_kit_orderpoints:
            dummy, bom_sub_lines = bom_kit_orderpoints[orderpoint].explode(orderpoint.product_id, 1)
            ratios_qty_available = []
            # total = qty_available + in_progress
            ratios_total = []
            for bom_line, bom_line_data in bom_sub_lines:
                component = bom_line.product_id
                if not component.is_storable or bom_line.product_uom_id.is_zero(bom_line_data['qty']):
                    continue
                uom_qty_per_kit = bom_line_data['qty'] / bom_line_data['original_qty']
                qty_per_kit = bom_line.product_uom_id._compute_quantity(uom_qty_per_kit, bom_line.product_id.uom_id, raise_if_failure=False)
                if not qty_per_kit:
                    continue
                qty_by_product_location, dummy = component._get_quantity_in_progress(orderpoint.location_id.ids)
                qty_in_progress = qty_by_product_location.get((component.id, orderpoint.location_id.id), 0.0)
                qty_available = component.qty_available / qty_per_kit
                ratios_qty_available.append(qty_available)
                ratios_total.append(qty_available + (qty_in_progress / qty_per_kit))
            # For a kit, the quantity in progress is :
            #  (the quantity if we have received all in-progress components) - (the quantity using only available components)
            product_qty = min(ratios_total or [0]) - min(ratios_qty_available or [0])
            res[orderpoint.id] = orderpoint.product_id.uom_id._compute_quantity(product_qty, orderpoint.product_uom, round=False)

        bom_manufacture = self.env['mrp.bom']._bom_find(orderpoints_without_kit.product_id, bom_type='normal')
        bom_manufacture = self.env['mrp.bom'].concat(*bom_manufacture.values())
        # add quantities coming from draft MOs
        productions_group = self.env['mrp.production']._read_group(
            [
                ('bom_id', 'in', bom_manufacture.ids),
                ('state', '=', 'draft'),
                ('orderpoint_id', 'in', orderpoints_without_kit.ids),
                ('id', 'not in', self.env.context.get('ignore_mo_ids', [])),
            ],
            ['orderpoint_id', 'product_uom_id'],
            ['product_qty:sum'])
        for orderpoint, uom, product_qty_sum in productions_group:
            res[orderpoint.id] += uom._compute_quantity(
                product_qty_sum, orderpoint.product_uom, round=False)

        # add quantities coming from confirmed MO to be started but not finished
        # by the end of the stock forecast
        in_progress_productions = self.env['mrp.production'].search([
            ('bom_id', 'in', bom_manufacture.ids),
            ('state', '=', 'confirmed'),
            ('orderpoint_id', 'in', orderpoints_without_kit.ids),
            ('id', 'not in', self.env.context.get('ignore_mo_ids', [])),
        ])
        for prod in in_progress_productions:
            date_start, date_finished, orderpoint = prod.date_start, prod.date_finished, prod.orderpoint_id
            lead_horizon_date = datetime.combine(orderpoint.lead_horizon_date, time.max)
            if date_start <= lead_horizon_date < date_finished:
                res[orderpoint.id] += prod.product_uom_id._compute_quantity(
                        prod.product_qty, orderpoint.product_uom, round=False)
        return res