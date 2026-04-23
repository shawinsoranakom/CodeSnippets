def _get_quantities_info(self, product, bom_uom, product_info, parent_bom=False, parent_product=False):
        quantities_info = super()._get_quantities_info(product, bom_uom, product_info, parent_bom, parent_product)
        if parent_product and parent_bom and parent_bom.type == 'subcontract' and product.is_storable:
            route_info = product_info.get(parent_product.id, {}).get(parent_bom.id, {})
            if route_info and route_info['route_type'] == 'subcontract':
                subcontracting_loc = route_info['supplier'].partner_id.property_stock_subcontractor
                subloc_product = product.with_context(location=subcontracting_loc.id, warehouse_id=False)
                subloc_product.fetch(['free_qty', 'qty_available'])
                stock_loc = f"subcontract_{subcontracting_loc.id}"
                if not product_info[product.id]['consumptions'].get(stock_loc, False):
                    product_info[product.id]['consumptions'][stock_loc] = 0
                quantities_info['free_to_manufacture_qty'] = product.uom_id._compute_quantity(subloc_product.free_qty, bom_uom)
                quantities_info['free_qty'] = quantities_info['free_to_manufacture_qty']
                quantities_info['on_hand_qty'] = product.uom_id._compute_quantity(subloc_product.qty_available, bom_uom)
                quantities_info['stock_loc'] = stock_loc

        return quantities_info