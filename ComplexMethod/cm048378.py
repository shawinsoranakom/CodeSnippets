def _apply_dest_to_package(self, processed_package_ids=None):
        """ Moves the packages to their new container and checks that no contained quants of the new container
            would be in different locations.
        """
        packages_todo = self
        if processed_package_ids:
            packages_todo = packages_todo.filtered(lambda p: p.id not in processed_package_ids)
        else:
            processed_package_ids = set()
        packs_by_container = packages_todo.grouped('package_dest_id')
        for container_package, packages in packs_by_container.items():
            if not container_package:
                # If package has no future container package, needs to be removed from its current one.
                packages.write({'parent_package_id': False})
                processed_package_ids.update(packages.ids)
                continue
            # At this point, the packages were already moved so we need to check their current position.
            new_location = packages.location_id
            if len(new_location) > 1:
                raise UserError(self.env._("Packages %(duplicate_names)s are moved to different locations while being in the same container %(container_name)s.",
                                            duplicate_names=packages.mapped('name'), container_name=container_package.name))
            contained_quants = container_package.contained_quant_ids.filtered(lambda q: not float_is_zero(q.quantity, precision_rounding=q.product_uom_id.rounding))
            if contained_quants and contained_quants.location_id != new_location:
                old_location = contained_quants.location_id - new_location
                raise UserError(self.env._("Can't move a container having packages in another location (%(old_location)s) to a different location (%(new_location)s).",
                                            old_location=old_location.display_name, new_location=new_location.display_name))
            packages.write({
                'parent_package_id': container_package.id,
                'package_dest_id': False,
            })
            processed_package_ids.update(packages.ids)
        # First level has been applied, need to check if next level needs to be applied as well.
        if packages_todo.parent_package_id.package_dest_id or packages_todo.parent_package_id.parent_package_id:
            packages_todo.parent_package_id._apply_dest_to_package(processed_package_ids)