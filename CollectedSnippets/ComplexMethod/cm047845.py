def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        """ When the product is a kit, this override computes the fields :
         - 'virtual_available'
         - 'qty_available'
         - 'incoming_qty'
         - 'outgoing_qty'
         - 'free_qty'

        This override is used to get the correct quantities of products
        with 'phantom' as BoM type.
        """
        bom_kits = self.env['mrp.bom']._bom_find(self, bom_type='phantom')
        kits = self.filtered(lambda p: bom_kits.get(p))
        regular_products = self - kits
        res = (
            super(ProductProduct, regular_products)._compute_quantities_dict(lot_id, owner_id, package_id, from_date=from_date, to_date=to_date)
            if regular_products
            else {}
        )
        qties = self.env.context.get("mrp_compute_quantities", {})
        qties.update(res)
        # pre-compute bom lines and identify missing kit components to prefetch
        bom_sub_lines_per_kit = {}
        prefetch_component_ids = set()
        for product in bom_kits:
            __, bom_sub_lines = bom_kits[product].explode(product, 1)
            bom_sub_lines_per_kit[product] = bom_sub_lines
            for bom_line, __ in bom_sub_lines:
                if bom_line.product_id.id not in qties:
                    prefetch_component_ids.add(bom_line.product_id.id)
        # compute kit quantities
        for product in bom_kits:
            bom_sub_lines = bom_sub_lines_per_kit[product]
            # group lines by component
            bom_sub_lines_grouped = collections.defaultdict(list)
            for info in bom_sub_lines:
                bom_sub_lines_grouped[info[0].product_id].append(info)
            ratios_virtual_available = []
            ratios_qty_available = []
            ratios_incoming_qty = []
            ratios_outgoing_qty = []
            ratios_free_qty = []

            for component, bom_sub_lines in bom_sub_lines_grouped.items():
                component = component.with_context(mrp_compute_quantities=qties).with_prefetch(prefetch_component_ids)
                qty_per_kit = 0
                for bom_line, bom_line_data in bom_sub_lines:
                    if not component.is_storable or bom_line.product_uom_id.is_zero(bom_line_data['qty']):
                        # As BoMs allow components with 0 qty, a.k.a. optionnal components, we simply skip those
                        # to avoid a division by zero. The same logic is applied to non-storable products as those
                        # products have 0 qty available.
                        continue
                    uom_qty_per_kit = bom_line_data['qty'] / bom_line_data['original_qty']
                    qty_per_kit += bom_line.product_uom_id._compute_quantity(uom_qty_per_kit, bom_line.product_id.uom_id, round=False, raise_if_failure=False)
                if not qty_per_kit:
                    continue
                component_res = (
                    qties.get(component.id)
                    if component.id in qties
                    else {
                        "virtual_available": component.uom_id.round(component.virtual_available),
                        "qty_available": component.uom_id.round(component.qty_available),
                        "incoming_qty": component.uom_id.round(component.incoming_qty),
                        "outgoing_qty": component.uom_id.round(component.outgoing_qty),
                        "free_qty": component.uom_id.round(component.free_qty),
                    }
                )
                ratios_virtual_available.append(component.uom_id.round(component_res["virtual_available"] / qty_per_kit, rounding_method='DOWN'))
                ratios_qty_available.append(component.uom_id.round(component_res["qty_available"] / qty_per_kit, rounding_method='DOWN'))
                ratios_incoming_qty.append(component.uom_id.round(component_res["incoming_qty"] / qty_per_kit, rounding_method='DOWN'))
                ratios_outgoing_qty.append(component.uom_id.round(component_res["outgoing_qty"] / qty_per_kit, rounding_method='DOWN'))
                ratios_free_qty.append(component.uom_id.round(component_res["free_qty"] / qty_per_kit, rounding_method='DOWN'))
            if bom_sub_lines and ratios_virtual_available:  # Guard against all cnsumable bom: at least one ratio should be present.
                res[product.id] = {
                    'virtual_available': component.uom_id.round(min(ratios_virtual_available) * bom_kits[product].product_qty) // 1,
                    'qty_available': component.uom_id.round(min(ratios_qty_available) * bom_kits[product].product_qty) // 1,
                    'incoming_qty': component.uom_id.round(min(ratios_incoming_qty) * bom_kits[product].product_qty) // 1,
                    'outgoing_qty': component.uom_id.round(min(ratios_outgoing_qty) * bom_kits[product].product_qty) // 1,
                    'free_qty': component.uom_id.round(min(ratios_free_qty) * bom_kits[product].product_qty) // 1,
                }
            else:
                res[product.id] = {
                    'virtual_available': 0,
                    'qty_available': 0,
                    'incoming_qty': 0,
                    'outgoing_qty': 0,
                    'free_qty': 0,
                }

        return res