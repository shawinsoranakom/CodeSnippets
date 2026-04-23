def _update_name_and_code(self, new_name=False, new_code=False):
        if new_code:
            self.mapped('lot_stock_id').mapped('location_id').write({'name': new_code})
        if new_name:
            # TDE FIXME: replacing the route name ? not better to re-generate the route naming ?
            for warehouse in self:
                routes = warehouse.route_ids
                for route in routes:
                    route.write({'name': route.name.replace(warehouse.name, new_name, 1)})
                    for pull in route.rule_ids:
                        pull.write({'name': pull.name.replace(warehouse.name, new_name, 1)})
                if warehouse.mto_pull_id:
                    warehouse.mto_pull_id.write({'name': warehouse.mto_pull_id.name.replace(warehouse.name, new_name, 1)})
        for warehouse in self:
            sequence_data = warehouse._get_sequence_values(name=new_name, code=new_code)
            # `ir.sequence` write access is limited to system user
            if self.env.user.has_group('stock.group_stock_manager'):
                warehouse = warehouse.sudo()
            warehouse.in_type_id.sequence_id.write(sequence_data['in_type_id'])
            warehouse.qc_type_id.sequence_id.write(sequence_data['qc_type_id'])
            warehouse.store_type_id.sequence_id.write(sequence_data['store_type_id'])
            warehouse.out_type_id.sequence_id.write(sequence_data['out_type_id'])
            warehouse.pack_type_id.sequence_id.write(sequence_data['pack_type_id'])
            warehouse.pick_type_id.sequence_id.write(sequence_data['pick_type_id'])
            warehouse.int_type_id.sequence_id.write(sequence_data['int_type_id'])
            warehouse.xdock_type_id.sequence_id.write(sequence_data['xdock_type_id'])