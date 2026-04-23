def _compute_package_info(self):
        for package in self:
            package.location_id = False
            package.company_id = False
            quants = package.quant_ids.filtered(lambda q: q.product_uom_id.compare(q.quantity, 0) > 0)
            if quants:
                package.location_id = quants[0].location_id
                if all(q.company_id == quants[0].company_id for q in package.quant_ids):
                    package.company_id = quants[0].company_id
            elif package.child_package_ids:
                package.location_id = package.child_package_ids[0].location_id
                if all(p.company_id == package.child_package_ids[0].company_id for p in package.child_package_ids):
                    package.company_id = package.child_package_ids[0].company_id