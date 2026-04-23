def _adjust_procure_method(self, picking_type_code=False):
        """ This method will try to apply the procure method MTO on some moves if
        a compatible MTO route is found. Else the procure method will be set to MTS
        picking_type_code (str, optional): Adjusts the procurement method based on
            the specified picking type code. The code to specify the picking type for
            the procurement group. Defaults to False.
        """
        # Prepare the MTSO variables. They are needed since MTSO moves are handled separately.
        # We need 2 dicts:
        # - needed quantity per location per product
        # - forecasted quantity per location per product

        for move in self:
            product_id = move.product_id
            location = move.location_id
            while location:
                domain = [
                    ('location_src_id', '=', location.id),
                    ('location_dest_id', '=', move.location_dest_id.id),
                    ('action', '!=', 'push')
                ]
                if picking_type_code:
                    domain.append(('picking_type_id.code', '=', picking_type_code))
                rule = self.env['stock.rule']._search_rule(False, move.packaging_uom_id, product_id, move.warehouse_id or move.picking_type_id.warehouse_id, domain)
                if rule:
                    break
                location = location.location_id
            if not rule:
                move.procure_method = 'make_to_stock'
                continue

            move.rule_id = rule.id
            if rule.procure_method in ['make_to_stock', 'make_to_order']:
                move.procure_method = rule.procure_method
            else:
                move.procure_method = 'make_to_stock'