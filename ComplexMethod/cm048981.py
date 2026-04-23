def action_merge(self):
        if not self:
            return
        if len(self) < 2:
            raise UserError(self.env._('Please select at least two batch/wave transfers to merge.'))
        if len(self.picking_type_id) > 1:
            raise UserError(_('Batch/Wave transfers with different operation types cannot be merged.'))
        if len(set(self.mapped('is_wave'))) > 1:
            raise UserError(_('Batch transfers cannot be merged with wave transfers and vice versa.'))
        if len(set(self.mapped('state'))) > 1:
            raise UserError(_('Batch/Wave transfers with different states cannot be merged.'))
        if self[0].state in ['done', 'cancel']:
            raise UserError(_('You cannot merge done or cancelled batch/wave transfers.'))

        target_batch = self[:1]
        other_batches = self[1:]
        earliest_batch = self.filtered(lambda b: b.scheduled_date).sorted(key=lambda b: b.scheduled_date)[0]
        merged_batch_vals = earliest_batch._get_merged_batch_vals()
        target_batch.move_line_ids |= other_batches.move_line_ids
        target_batch.picking_ids |= other_batches.picking_ids
        target_batch.write(merged_batch_vals)
        other_batches.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Batch/Wave transfers have been merged into the following transfer'),
                'message': '%s',
                'links': [{
                    'label': target_batch.name,
                    'url': f"/odoo/action-stock_picking_batch.{'action_picking_tree_wave' if target_batch.is_wave else 'stock_picking_batch_action'}/{target_batch.id}",
                }],
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }