def _format_route_info(self, rules, rules_delay, warehouse, product, bom, quantity):
        res = super()._format_route_info(rules, rules_delay, warehouse, product, bom, quantity)
        subcontract_rules = [rule for rule in rules if rule.action == 'buy' and bom and bom.type == 'subcontract']
        if subcontract_rules:
            supplier = product._select_seller(quantity=quantity, uom_id=product.uom_id, params={'subcontractor_ids': bom.subcontractor_ids})
            if not supplier:
                # If no vendor found for the right quantity, we still want to display a vendor for the lead times
                supplier = product._select_seller(quantity=None, uom_id=product.uom_id, params={'subcontractor_ids': bom.subcontractor_ids})
            # for subcontracting, we can't decide the lead time without component's resupply availability
            # we only return necessary info and calculate the lead time late when we have component's data
            if supplier:
                qty_supplier_uom = product.uom_id._compute_quantity(quantity, supplier.product_uom_id)
                return {
                    'route_type': 'subcontract',
                    'route_name': subcontract_rules[0].route_id.display_name,
                    'route_detail': supplier.with_context(use_simplified_supplier_name=True).display_name,
                    'lead_time': rules_delay,
                    'supplier': supplier,
                    'route_alert': product.uom_id.compare(qty_supplier_uom, supplier.min_qty) < 0,
                    'qty_checked': quantity,
                    'bom': bom,
                }

        return res