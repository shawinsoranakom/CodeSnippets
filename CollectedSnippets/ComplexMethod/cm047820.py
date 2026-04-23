def _compute_qty_ready(self):
        for workorder in self:
            if workorder.state in ('cancel', 'done'):
                workorder.qty_ready = 0
                continue
            if not workorder.blocked_by_workorder_ids or all(wo.state == 'cancel' for wo in workorder.blocked_by_workorder_ids):
                workorder.qty_ready = workorder.qty_remaining
                continue
            workorder_qty_ready = workorder.qty_remaining + workorder.qty_produced
            for wo in workorder.blocked_by_workorder_ids:
                if wo.state != 'cancel':
                    workorder_qty_ready = min(workorder_qty_ready, wo.qty_produced + wo.qty_reported_from_previous_wo)
            workorder.qty_ready = workorder_qty_ready - workorder.qty_produced - workorder.qty_reported_from_previous_wo