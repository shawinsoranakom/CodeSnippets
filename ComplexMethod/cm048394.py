def set_values(self):
        warehouse_grp = self.env.ref('stock.group_stock_multi_warehouses')
        location_grp = self.env.ref('stock.group_stock_multi_locations')
        base_user = self.env.ref('base.group_user')
        base_user_implied_ids = base_user.implied_ids
        if not self.group_stock_multi_locations and location_grp in base_user_implied_ids and warehouse_grp in base_user_implied_ids:
            raise UserError(_("You can't deactivate the multi-location if you have more than once warehouse by company"))

        previous_group = self.default_get(['group_stock_multi_locations', 'group_stock_production_lot', 'group_stock_tracking_lot'])
        super().set_values()

        if not self.env.user.has_group('stock.group_stock_manager'):
            return

        # If we just enabled multiple locations with this settings change, we can deactivate
        # the internal operation types of the warehouses, so they won't appear in the dashboard.
        # Otherwise (if we just disabled multiple locations with this settings change), activate them
        warehouse_obj = self.env['stock.warehouse']
        if self.group_stock_multi_locations and not previous_group.get('group_stock_multi_locations'):
            # override active_test that is false in set_values
            warehouse_obj.with_context(active_test=True).search([]).int_type_id.active = True
            # Disable the views removing the create button from the location list and form.
            # Be resilient if the views have been deleted manually.
            for view in (
                self.env.ref('stock.stock_location_view_tree2_editable', raise_if_not_found=False),
                self.env.ref('stock.stock_location_view_form_editable', raise_if_not_found=False),
            ):
                if view:
                    view.active = False
        elif not self.group_stock_multi_locations and previous_group.get('group_stock_multi_locations'):
            warehouse_obj.search([
                ('reception_steps', '=', 'one_step'),
                ('delivery_steps', '=', 'ship_only')
            ]).int_type_id.active = False
            # Enable the views removing the create button from the location list and form.
            # Be resilient if the views have been deleted manually.
            for view in (
                self.env.ref('stock.stock_location_view_tree2_editable', raise_if_not_found=False),
                self.env.ref('stock.stock_location_view_form_editable', raise_if_not_found=False),
            ):
                if view:
                    view.active = True

        if not self.group_stock_production_lot and previous_group.get('group_stock_production_lot'):
            if self.env['product.product'].search_count([('tracking', '!=', 'none')], limit=1):
                raise UserError(_("You have product(s) in stock that have lot/serial number tracking enabled. \nSwitch off tracking on all the products before switching off this setting."))

        return