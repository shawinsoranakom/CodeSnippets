def button_validate(self):
        res = super().button_validate()
        to_assign_ids = set()
        # Having non-done pickings after the `super()` call means it stopped early,
        # so we shouldn’t remove the pickings from batches yet.
        if not any(picking.state == 'done' for picking in self):
            return res
        if self and self.env.context.get('pickings_to_detach'):
            pickings_to_detach = self.env['stock.picking'].browse(self.env.context['pickings_to_detach'])
            pickings_to_detach.batch_id = False
            pickings_to_detach.move_ids.filtered(lambda m: not m.quantity).picked = False
            to_assign_ids.update(self.env.context['pickings_to_detach'])

        for picking in self:
            if picking.state != 'done':
                continue
            # Avoid inconsistencies in states of the same batch when validating a single picking in a batch.
            if picking.batch_id and any(p.state != 'done' for p in picking.batch_id.picking_ids):
                picking.batch_id = None
            # If backorder were made, if auto-batch is enabled, seek a batch for each of them with the selected criterias.
            to_assign_ids.update(picking.backorder_ids.ids)

        # To avoid inconsistencies, all incorrect pickings must be removed before assigning backorder pickings
        assignable_pickings = self.env['stock.picking'].browse(to_assign_ids)
        for picking in assignable_pickings:
            picking._find_auto_batch()
        assignable_pickings.move_line_ids.with_context(skip_auto_waveable=True)._auto_wave()

        return res