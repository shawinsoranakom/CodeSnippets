def write(self, vals):
        if 'company_id' in vals:
            for warehouse in self:
                if warehouse.company_id.id != vals['company_id']:
                    raise UserError(_("Changing the company of this record is forbidden at this point, you should rather archive it and create a new one."))

        Route = self.env['stock.route']
        warehouses = self.with_context(active_test=False)
        warehouses._create_missing_locations(vals)

        if vals.get('reception_steps'):
            warehouses._update_location_reception(vals['reception_steps'])
        if vals.get('delivery_steps'):
            warehouses._update_location_delivery(vals['delivery_steps'])
        if vals.get('reception_steps') or vals.get('delivery_steps'):
            warehouses._update_reception_delivery_resupply(vals.get('reception_steps'), vals.get('delivery_steps'))

        if vals.get('resupply_wh_ids') and not vals.get('resupply_route_ids'):
            old_resupply_whs = {warehouse.id: warehouse.resupply_wh_ids for warehouse in warehouses}

        # If another partner assigned
        if vals.get('partner_id'):
            if vals.get('company_id'):
                warehouses._update_partner_data(vals['partner_id'], vals.get('company_id'))
            else:
                for warehouse in self:
                    warehouse._update_partner_data(vals['partner_id'], warehouse.company_id.id)

        if vals.get('code') or vals.get('name'):
            warehouses._update_name_and_code(vals.get('name'), vals.get('code'))

        res = super().write(vals)

        for warehouse in warehouses:
            # check if we need to delete and recreate route
            depends = [depend for depends in [value.get('depends', []) for value in warehouse._get_routes_values().values()] for depend in depends]
            if 'code' in vals or any(depend in vals for depend in depends):
                picking_type_vals = warehouse._create_or_update_sequences_and_picking_types()
                if picking_type_vals:
                    warehouse.write(picking_type_vals)
            if any(depend in vals for depend in depends):
                route_vals = warehouse._create_or_update_route()
                if route_vals:
                    warehouse.write(route_vals)
            # Check if a global rule(mto, buy, ...) need to be modify.
            # The field that impact those rules are listed in the
            # _get_global_route_rules_values method under the key named
            # 'depends'.
            global_rules = warehouse._get_global_route_rules_values()
            depends = [depend for depends in [value.get('depends', []) for value in global_rules.values()] for depend in depends]
            if any(rule in vals for rule in global_rules) or\
                    any(depend in vals for depend in depends):
                warehouse._create_or_update_global_routes_rules()

            if 'active' in vals:
                picking_type_ids = self.env['stock.picking.type'].with_context(active_test=False).search([('warehouse_id', '=', warehouse.id)])
                move_ids = self.env['stock.move'].search([
                    ('picking_type_id', 'in', picking_type_ids.ids),
                    ('state', 'not in', ('done', 'cancel')),
                ])
                if move_ids:
                    raise UserError(_(
                        'You still have ongoing operations for operation types %(operations)s in warehouse %(warehouse)s',
                        operations=move_ids.mapped('picking_type_id.name'),
                        warehouse=warehouse.name,
                    ))
                else:
                    picking_type_ids.write({'active': vals['active']})
                location_ids = self.env['stock.location'].with_context(active_test=False).search([('location_id', 'child_of', warehouse.view_location_id.id)])
                picking_type_using_locations = self.env['stock.picking.type'].search([
                    ('default_location_src_id', 'in', location_ids.ids),
                    ('default_location_dest_id', 'in', location_ids.ids),
                    ('id', 'not in', picking_type_ids.ids),
                ])
                if picking_type_using_locations:
                    raise UserError(_(
                        '%(operations)s have default source or destination locations within warehouse %(warehouse)s, therefore you cannot archive it.',
                        operations=picking_type_using_locations.mapped('name'),
                        warehouse=warehouse.name,
                    ))
                warehouse.view_location_id.write({'active': vals['active']})

                rule_ids = self.env['stock.rule'].with_context(active_test=False).search([('warehouse_id', '=', warehouse.id)])
                # Only modify route that apply on this warehouse.
                warehouse.route_ids.filtered(lambda r: len(r.warehouse_ids) == 1).write({'active': vals['active']})
                rule_ids.write({'active': vals['active']})

                if warehouse.active:
                    # Catch all warehouse fields that trigger a modfication on
                    # routes, rules, picking types and locations (e.g the reception
                    # steps). The purpose is to write on it in order to let the
                    # write method set the correct field to active or archive.
                    depends = set([])
                    for rule_item in warehouse._get_global_route_rules_values().values():
                        for depend in rule_item.get('depends', []):
                            depends.add(depend)
                    for rule_item in warehouse._get_routes_values().values():
                        for depend in rule_item.get('depends', []):
                            depends.add(depend)
                    values = {'resupply_route_ids': [(4, route.id) for route in warehouse.resupply_route_ids]}
                    for depend in depends:
                        values.update({depend: warehouse[depend]})
                    warehouse.write(values)

        if vals.get('resupply_wh_ids') and not vals.get('resupply_route_ids'):
            for warehouse in warehouses:
                new_resupply_whs = warehouse.resupply_wh_ids
                to_add = new_resupply_whs - old_resupply_whs[warehouse.id]
                to_remove = old_resupply_whs[warehouse.id] - new_resupply_whs
                if to_add:
                    existing_routes = Route.search([
                        ('supplied_wh_id', '=', warehouse.id),
                        ('supplier_wh_id', 'in', to_add.ids),
                        ('active', '=', False)
                    ])
                    existing_routes.action_unarchive()
                    remaining_to_add = to_add - existing_routes.supplier_wh_id
                    if remaining_to_add:
                        warehouse.create_resupply_routes(remaining_to_add)
                if to_remove:
                    to_disable_route_ids = Route.search([
                        ('supplied_wh_id', '=', warehouse.id),
                        ('supplier_wh_id', 'in', to_remove.ids),
                        ('active', '=', True)
                    ])
                    to_disable_route_ids.action_archive()

        if 'active' in vals:
            self._check_multiwarehouse_group()
        return res