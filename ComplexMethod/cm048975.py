def _find_auto_batch(self):
        self.ensure_one()
        # Check if auto_batch is enabled for this picking.
        if not self.picking_type_id.auto_batch or not self.picking_type_id._is_auto_batch_grouped() or self.batch_id or not self.move_ids or not self._is_auto_batchable():
            return False

        # Try to find a compatible batch to insert the picking
        possible_batches = self.env['stock.picking.batch'].sudo().search(self._get_possible_batches_domain())
        for batch in possible_batches:
            if batch._is_picking_auto_mergeable(self):
                batch.picking_ids |= self
                return batch

        # If no batch were found, try to find a compatible picking and put them both in a new batch.
        possible_pickings = self.env['stock.picking'].search(self._get_possible_pickings_domain())
        new_batch_data = {
            'picking_ids': [Command.link(self.id)],
            'company_id': self.company_id.id if self.company_id else False,
            'picking_type_id': self.picking_type_id.id,
            'description': self._get_auto_batch_description()
        }
        for picking in possible_pickings:
            if self._is_auto_batchable(picking):
                # Add the picking to the new batch
                new_batch_data['picking_ids'].append(Command.link(picking.id))
                new_batch = self.env['stock.picking.batch'].sudo().create(new_batch_data)
                if picking.picking_type_id.batch_auto_confirm:
                    new_batch.action_confirm()
                return new_batch

        # If nothing was found after those two steps, then create a batch with the current picking alone
        new_batch_data['user_id'] = self.user_id.id
        new_batch = self.env['stock.picking.batch'].sudo().create(new_batch_data)
        if self.picking_type_id.batch_auto_confirm:
            new_batch.action_confirm()
        return new_batch