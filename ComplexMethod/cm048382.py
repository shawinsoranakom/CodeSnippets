def _create_or_update_sequences_and_picking_types(self):
        """ Create or update existing picking types for a warehouse.
        Pikcing types are stored on the warehouse in a many2one. If the picking
        type exist this method will update it. The update values can be found in
        the method _get_picking_type_update_values. If the picking type does not
        exist it will be created with a new sequence associated to it.
        """
        self.ensure_one()
        IrSequenceSudo = self.env['ir.sequence'].sudo()
        PickingType = self.env['stock.picking.type']

        # choose the next available color for the operation types of this warehouse
        all_used_colors = [res['color'] for res in PickingType.search_read([('warehouse_id', '!=', False), ('color', '!=', False)], ['color'], order='color')]
        available_colors = [zef for zef in range(0, 12) if zef not in all_used_colors]
        color = available_colors[0] if available_colors else 0

        warehouse_data = {}
        sequence_data = self._get_sequence_values()

        # suit for each warehouse: reception, internal, pick, pack, ship
        max_sequence = self.env['stock.picking.type'].search_read([('sequence', '!=', False)], ['sequence'], limit=1, order='sequence desc')
        max_sequence = max_sequence and max_sequence[0]['sequence'] or 0

        data = self._get_picking_type_update_values()
        create_data, max_sequence = self._get_picking_type_create_values(max_sequence)

        for picking_type, values in data.items():
            if self[picking_type]:
                self[picking_type].sudo().sequence_id.write({'company_id': self.company_id.id})
                self[picking_type].write(values)
            else:
                data[picking_type].update(create_data[picking_type])
                existing_sequence = IrSequenceSudo.search_count([('company_id', '=', sequence_data[picking_type]['company_id']), ('name', '=', sequence_data[picking_type]['name'])], limit=1)
                sequence = IrSequenceSudo.create(sequence_data[picking_type])
                if existing_sequence:
                    sequence.name = _("%(name)s (copy)(%(id)s)", name=sequence.name, id=str(sequence.id))
                values.update(warehouse_id=self.id, color=color, sequence_id=sequence.id)
                warehouse_data[picking_type] = PickingType.create(values).id

        if 'out_type_id' in warehouse_data:
            PickingType.browse(warehouse_data['out_type_id']).write({'return_picking_type_id': warehouse_data.get('in_type_id', False)})
        if 'in_type_id' in warehouse_data:
            PickingType.browse(warehouse_data['in_type_id']).write({'return_picking_type_id': warehouse_data.get('out_type_id', False)})
        return warehouse_data