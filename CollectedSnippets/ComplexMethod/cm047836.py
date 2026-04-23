def _compute_workorder_count(self):
        MrpWorkorder = self.env['mrp.workorder']
        result = {wid: {} for wid in self._ids}
        result_duration_expected = {wid: 0 for wid in self._ids}
        # Count Late Workorder
        data = MrpWorkorder._read_group(
            [('workcenter_id', 'in', self.ids), ('state', 'in', ('blocked', 'ready')), ('date_start', '<', datetime.now().strftime('%Y-%m-%d'))],
            ['workcenter_id'], ['__count'])
        count_data = {workcenter.id: count for workcenter, count in data}
        # Count All, Pending, Ready, Progress Workorder
        res = MrpWorkorder._read_group(
            [('workcenter_id', 'in', self.ids)],
            ['workcenter_id', 'state'], ['duration_expected:sum', '__count'])
        for workcenter, state, duration_sum, count in res:
            result[workcenter.id][state] = count
            if state in ('blocked', 'ready', 'progress'):
                result_duration_expected[workcenter.id] += duration_sum
        for workcenter in self:
            workcenter.workorder_count = sum(count for state, count in result[workcenter.id].items() if state not in ('done', 'cancel'))
            workcenter.workorder_blocked_count = result[workcenter.id].get('blocked', 0)
            workcenter.workcenter_load = result_duration_expected[workcenter.id]
            workcenter.workorder_ready_count = result[workcenter.id].get('ready', 0)
            workcenter.workorder_progress_count = result[workcenter.id].get('progress', 0)
            workcenter.workorder_late_count = count_data.get(workcenter.id, 0)