def _get_packages_from_picking(self, picking, default_package_type):
        packages = []

        if picking.is_return_picking:
            commodities = self._get_commodities_from_stock_move_lines(picking.move_line_ids)
            weight = picking._get_estimated_weight() + default_package_type.base_weight
            packages.append(DeliveryPackage(
                commodities,
                weight,
                default_package_type,
                currency=picking.company_id.currency_id,
                picking=picking,
            ))
            return packages

        # Create all packages.
        for package in picking.move_line_ids.result_package_id:
            move_lines = picking.move_line_ids.filtered(lambda ml: ml.result_package_id == package)
            commodities = self._get_commodities_from_stock_move_lines(move_lines)
            package_total_cost = 0.0
            for quant in package.quant_ids:
                package_total_cost += self._product_price_to_company_currency(
                    quant.quantity, quant.product_id, picking.company_id
                )
            packages.append(DeliveryPackage(
                commodities,
                package.shipping_weight or package.weight,
                package.package_type_id,
                name=package.name,
                total_cost=package_total_cost,
                currency=picking.company_id.currency_id,
                picking=picking,
            ))

        # Create one package: either everything is in pack or nothing is.
        if picking.weight_bulk:
            commodities = self._get_commodities_from_stock_move_lines(picking.move_line_ids)
            package_total_cost = 0.0
            for move_line in picking.move_line_ids:
                package_total_cost += self._product_price_to_company_currency(
                    move_line.quantity, move_line.product_id, picking.company_id
                )
            packages.append(DeliveryPackage(
                commodities,
                picking.weight_bulk,
                default_package_type,
                name='Bulk Content',
                total_cost=package_total_cost,
                currency=picking.company_id.currency_id,
                picking=picking,
            ))
        elif not packages:
            raise UserError(_(
                "The package cannot be created because the total weight of the "
                "products in the picking is 0.0 %s",
                picking.weight_uom_name
            ))
        return packages