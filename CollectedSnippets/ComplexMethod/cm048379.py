def create(self, vals_list):
        for vals in vals_list:
            if vals.get('company_id'):
                company = self.env['res.company'].browse(vals['company_id'])
                if 'name' not in vals:
                    vals['name'] = company.name
                if 'code' not in vals:
                    vals['code'] = company.name[:5]
                if 'partner_id' not in vals:
                    vals['partner_id'] = company.partner_id.id
            # create view location for warehouse then create all locations
            loc_vals = {'name': vals.get('code'), 'usage': 'view'}
            if vals.get('company_id'):
                loc_vals['company_id'] = vals.get('company_id')
            vals['view_location_id'] = self.env['stock.location'].create(loc_vals).id
            sub_locations = self._get_locations_values(vals)

            for field_name, values in sub_locations.items():
                values['location_id'] = vals['view_location_id']
                if vals.get('company_id'):
                    values['company_id'] = vals.get('company_id')
                vals[field_name] = self.env['stock.location'].with_context(active_test=False).create(values).id

        # actually create WH
        warehouses = super().create(vals_list)

        for warehouse, vals in zip(warehouses, vals_list):
            # create sequences and operation types
            new_vals = warehouse._create_or_update_sequences_and_picking_types()
            warehouse.write(new_vals)  # TDE FIXME: use super ?
            # create routes and push/stock rules
            route_vals = warehouse._create_or_update_route()
            warehouse.write(route_vals)

            # Update global route with specific warehouse rule.
            warehouse._create_or_update_global_routes_rules()

            # create route selectable on the product to resupply the warehouse from another one
            warehouse.create_resupply_routes(warehouse.resupply_wh_ids)

            # update partner data if partner assigned
            if vals.get('partner_id'):
                self._update_partner_data(vals['partner_id'], vals.get('company_id'))

            # manually update locations' warehouse since it didn't exist at their creation time
            view_location_id = self.env['stock.location'].browse(vals.get('view_location_id'))
            (view_location_id | view_location_id.with_context(active_test=False).child_ids).write({'warehouse_id': warehouse.id})

        self._check_multiwarehouse_group()

        return warehouses