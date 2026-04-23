def _compute_l10n_it_show_print_ddt_button(self):
        # Enable printing the DDT for done outgoing shipments
        # or dropshipping (picking going from supplier to customer)
        for picking in self:
            picking.l10n_it_show_print_ddt_button = (
                picking.country_code == 'IT'
                and picking.state == 'done'
                and picking.is_locked
                and (picking.picking_type_code == 'outgoing'
                     or (
                         picking.move_ids
                         and picking.move_ids[0].partner_id
                         and picking.location_id.usage == 'supplier'
                         and picking.location_dest_id.usage == 'customer'
                         )
                     )
                )