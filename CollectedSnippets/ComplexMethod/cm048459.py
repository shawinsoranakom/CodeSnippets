def _compute_show_details_visible(self):
        """ According to this field, the button that calls `action_show_details` will be displayed
        to work on a move from its picking form view, or not.
        """
        has_package = self.env.user.has_group('stock.group_tracking_lot')
        multi_locations_enabled = self.env.user.has_group('stock.group_stock_multi_locations')
        consignment_enabled = self.env.user.has_group('stock.group_tracking_owner')

        show_details_visible = multi_locations_enabled or has_package or consignment_enabled

        for move in self:
            if (
                not move.product_id
                or move.state == "draft"
                or (
                    not move.picking_type_id.use_create_lots
                    and not move.picking_type_id.use_existing_lots
                    and not self.env.user.has_group("stock.group_stock_tracking_lot")
                    and not self.env.user.has_group("stock.group_stock_multi_locations")
                )
            ):
                move.show_details_visible = False
            elif len(move.move_line_ids) > 1:
                move.show_details_visible = True
            else:
                move.show_details_visible = show_details_visible or move.has_tracking != 'none'