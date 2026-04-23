def _plan_workorders(self, replan=False):
        """ Plan all the production's workorders depending on the workcenters
        work schedule.

        :param replan: If it is a replan, only ready and blocked workorder will be taken into account
        :type replan: bool.
        """
        self.ensure_one()

        if not self.workorder_ids:
            self.is_planned = True
            return

        self._link_workorders_and_moves()

        # Plan workorders starting from final ones (those with no dependent workorders)
        final_workorders = self.workorder_ids.filtered(lambda wo: not wo.needed_by_workorder_ids)
        for workorder in final_workorders:
            workorder._plan_workorder(replan)

        workorders = self.workorder_ids.filtered(lambda w: w.state not in ['done', 'cancel'])
        if not workorders:
            return

        self.with_context(force_date=True).write({
            'date_start': min((workorder.leave_id.date_from for workorder in workorders if workorder.leave_id), default=None),
            'date_finished': max((workorder.leave_id.date_to for workorder in workorders if workorder.leave_id), default=None),
        })