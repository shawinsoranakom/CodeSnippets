def _get_weight(self, picking_id=False):
        res = {}
        if picking_id:
            package_weights = defaultdict(float)
            # If we check the weight of an ongoing package, we may need to check its current child dest as well to known their own weight.
            children_by_dest_pack, all_pack_ids = self._get_all_children_package_dest_ids()
            base_weight_per_package_group = self.env['stock.package']._read_group(
                domain=[('id', 'in', all_pack_ids)],
                groupby=['id', 'package_type_id.base_weight']
            )
            base_weight_per_package = {pack.id: weight for pack, weight in base_weight_per_package_group}

            res_groups = self.env['stock.move.line']._read_group(
                [('result_package_id', 'in', all_pack_ids), ('product_id', '!=', False), ('picking_id', '=', picking_id)],
                ['result_package_id', 'product_id', 'product_uom_id', 'quantity'],
                ['__count'],
            )
            for result_package, product, product_uom, quantity, count in res_groups:
                package_weights[result_package.id] += (
                    count
                    * product_uom._compute_quantity(quantity, product.uom_id)
                    * product.weight
                )
        for package in self:
            weight = package.package_type_id.base_weight or 0.0
            if picking_id:
                res[package] = weight + package_weights[package.id]
                for child_id in children_by_dest_pack.get(package, []):
                    res[package] += base_weight_per_package.get(child_id, 0) + package_weights.get(child_id, 0)
            else:
                # Take the base_weight of every contained package, so we include package only containing packages
                weight += sum(package.all_children_package_ids.mapped(lambda p: p.package_type_id.base_weight))
                for quant in package.contained_quant_ids:
                    weight += quant.quantity * quant.product_id.weight
                res[package] = weight
        return res