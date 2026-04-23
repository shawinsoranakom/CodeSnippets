def _apply_putaway_strategy(self):
        if self.env.context.get('avoid_putaway_rules'):
            return
        self = self.with_context(do_not_unreserve=True)
        for (package), smls in groupby(self, lambda sml: (sml.result_package_id.outermost_package_id)):
            smls = self.env['stock.move.line'].concat(*smls)
            locations = smls.move_id.location_dest_id.child_internal_location_ids
            excluded_smls = set(smls.ids)
            if package.package_type_id:
                best_loc = smls.move_id.location_dest_id.with_context(exclude_sml_ids=excluded_smls, products=smls.product_id, locations=locations)._get_putaway_strategy(self.env['product.product'], package=package)
                smls.location_dest_id = best_loc
            elif package:
                used_locations = set()
                for sml in smls:
                    if len(used_locations) > 1:
                        break
                    sml.location_dest_id = sml.move_id.location_dest_id.with_context(exclude_sml_ids=excluded_smls, locations=locations)._get_putaway_strategy(sml.product_id, quantity=sml.quantity)
                    excluded_smls.discard(sml.id)
                    used_locations.add(sml.location_dest_id)
                if len(used_locations) > 1:
                    for move, grouped_smls in smls.grouped('move_id').items():
                        grouped_smls.location_dest_id = move.location_dest_id
            else:
                for sml in smls:
                    putaway_loc_id = sml.move_id.location_dest_id.with_context(exclude_sml_ids=excluded_smls)._get_putaway_strategy(
                        sml.product_id, quantity=sml.quantity, packaging=sml.move_id.packaging_uom_id,
                    )
                    if putaway_loc_id != sml.location_dest_id:
                        sml.location_dest_id = putaway_loc_id
                    excluded_smls.discard(sml.id)