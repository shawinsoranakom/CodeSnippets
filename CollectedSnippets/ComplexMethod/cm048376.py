def write(self, vals):
        if 'name' in vals and not vals.get('name'):
            # Recomputes the name according the sequence if the name was emptied.
            package_type = self.env['stock.package.type'].browse(vals.get('package_type_id'))
            for package in self:
                package_type = self.env['stock.package.type'].browse(vals.get('package_type_id', self.package_type_id.id))
                package.name = package_type._get_next_name_by_sequence()
            del vals['name']
        if 'location_id' in vals:
            is_pack_empty = any(not pack.contained_quant_ids for pack in self)
            if not vals['location_id'] and not is_pack_empty:
                raise UserError(self.env._('Cannot remove the location of a non empty package'))
            elif vals['location_id']:
                if is_pack_empty:
                    raise UserError(self.env._('Cannot move an empty package'))
                # create a move from the old location to new location
                location_dest_id = self.env['stock.location'].browse(vals['location_id'])
                quant_to_move = self.contained_quant_ids.filtered(lambda q: q.quantity > 0)
                quant_to_move.move_quants(location_dest_id, message=self.env._('Package manually relocated'), up_to_parent_packages=self)
        if vals.get('package_dest_id'):
            # Need to make sure we avoid a recursion within the package dests. Can't rely on the `parent_path` for destination packages.
            current_children_dest_ids = self._get_all_children_package_dest_ids()[1]
            if vals['package_dest_id'] in current_children_dest_ids:
                raise ValidationError(self.env._("A package can't have one of its contained packages as destination container."))

        return super().write(vals)