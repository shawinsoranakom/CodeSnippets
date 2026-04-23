def _link_workorders_and_moves(self):
        self.ensure_one()
        if not self.workorder_ids:
            return
        workorder_per_operation = {workorder.operation_id: workorder for workorder in self.workorder_ids}
        workorder_boms = self.workorder_ids.operation_id.bom_id
        last_workorder_per_bom = defaultdict(lambda: self.env['mrp.workorder'])
        self.allow_workorder_dependencies = self.bom_id.allow_operation_dependencies

        def workorder_order(wo):
            return (wo.sequence, wo.id)

        if self.allow_workorder_dependencies:
            for workorder in self.workorder_ids.sorted(workorder_order):
                workorder.blocked_by_workorder_ids = [Command.link(workorder_per_operation[operation_id].id)
                                                      for operation_id in
                                                      workorder.operation_id.blocked_by_operation_ids
                                                      if operation_id in workorder_per_operation]
                if not workorder.needed_by_workorder_ids:
                    last_workorder_per_bom[workorder.operation_id.bom_id] = workorder
        else:
            previous_workorder = False
            for workorder in self.workorder_ids.sorted(workorder_order):
                if previous_workorder:
                    workorder.blocked_by_workorder_ids = [Command.link(previous_workorder.id)]
                previous_workorder = workorder
                last_workorder_per_bom[workorder.operation_id.bom_id] = workorder
        for move in (self.move_raw_ids | self.move_finished_ids):
            if move.operation_id:
                move.write({
                    'workorder_id': workorder_per_operation[move.operation_id].id if move.operation_id in workorder_per_operation else False
                })