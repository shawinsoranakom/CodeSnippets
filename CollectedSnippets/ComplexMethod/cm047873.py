def _format_state(self, record, components=False):
        """ For MOs, provide a custom state based on the demand vs quantities available for components.
        All other records types will provide their standard state value.
        :param dict components: components in the structure provided by `_get_components_data`
        :return: string to be used as custom state
        """
        if record._name != 'mrp.production' or record.state not in ('draft', 'confirmed') or not components:
            return dict(record._fields['state']._description_selection(self.env)).get(record.state)
        components_qty_to_produce = defaultdict(float)
        components_qty_reserved = defaultdict(float)
        components_qty_free = defaultdict(float)
        for component in components:
            component = component["summary"]
            product = component["product"]
            if not product.is_storable:
                continue
            uom = component["uom"]
            components_qty_to_produce[product] += uom._compute_quantity(component["quantity"], product.uom_id)
            components_qty_reserved[product] += uom._compute_quantity(component["quantity_reserved"], product.uom_id)
            components_qty_free[product] = uom._compute_quantity(component["quantity_free"], product.uom_id)
        producible_qty = record.product_qty
        for product, comp_qty_to_produce in components_qty_to_produce.items():
            if product.uom_id.is_zero(comp_qty_to_produce):
                continue
            comp_producible_qty = record.product_uom_id.round(
                record.product_qty * (components_qty_reserved[product] + components_qty_free[product]) / comp_qty_to_produce,
                rounding_method='DOWN',
            )
            if record.product_uom_id.compare(comp_producible_qty, 0) <= 0:
                return _("Not Ready")
            producible_qty = min(comp_producible_qty, producible_qty)
        if record.product_uom_id.compare(producible_qty, 0) <= 0:
            return _("Not Ready")
        elif record.product_uom_id.compare(producible_qty, record.product_qty) == -1:
            producible_qty = float_repr(producible_qty, self.env['decimal.precision'].precision_get('Product Unit'))
            return _("%(producible_qty)s Ready", producible_qty=producible_qty)
        return _("Ready")