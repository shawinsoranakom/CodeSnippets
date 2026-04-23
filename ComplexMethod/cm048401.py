def _get_putaway_location(self, product, quantity=0, package=None, packaging=None, qty_by_location=None):
        # find package type on package or packaging
        package_type = self.env['stock.package.type']
        if package:
            package_type = package.package_type_id
        elif packaging:
            package_type = packaging.package_type_id

        checked_locations = set()
        for putaway_rule in self:
            location_out = putaway_rule.location_out_id
            if putaway_rule.sublocation == 'last_used':
                location_dest_id = putaway_rule._get_last_used_location(product)
                location_out = location_dest_id or location_out

            child_locations = location_out.child_internal_location_ids

            if not putaway_rule.storage_category_id:
                if location_out in checked_locations:
                    continue
                if location_out._check_can_be_used(product, quantity, package, qty_by_location[location_out.id]):
                    return location_out
                continue
            else:
                child_locations = child_locations.filtered(lambda loc: loc.storage_category_id == putaway_rule.storage_category_id)

            # check if already have the product/package type stored
            for location in child_locations:
                if location in checked_locations:
                    continue
                if package_type:
                    if location.quant_ids.filtered(lambda q: q.package_id and q.package_id.package_type_id == package_type):
                        if location._check_can_be_used(product, quantity, package=package, location_qty=qty_by_location[location.id]):
                            return location
                        else:
                            checked_locations.add(location)
                elif product.uom_id.compare(qty_by_location[location.id], 0) > 0:
                    if location._check_can_be_used(product, quantity, location_qty=qty_by_location[location.id]):
                        return location
                    else:
                        checked_locations.add(location)

            # check locations with matched storage category
            for location in child_locations.filtered(lambda l: l.storage_category_id == putaway_rule.storage_category_id):
                if location in checked_locations:
                    continue
                if location._check_can_be_used(product, quantity, package, qty_by_location[location.id]):
                    return location
                checked_locations.add(location)

        return None