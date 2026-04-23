def _compute_can_be_marked_as_done(self):
        if not any(self._ids):
            for milestone in self:
                milestone.can_be_marked_as_done = not milestone.is_reached and all(milestone.task_ids.mapped(lambda t: t.is_closed))
            return

        unreached_milestones = self.filtered(lambda milestone: not milestone.is_reached)
        (self - unreached_milestones).can_be_marked_as_done = False
        task_read_group = self.env['project.task']._read_group(
            [('milestone_id', 'in', unreached_milestones.ids)],
            ['milestone_id', 'state'],
            ['__count'],
        )
        task_count_per_milestones = defaultdict(lambda: (0, 0))
        for milestone, state, count in task_read_group:
            opened_task_count, closed_task_count = task_count_per_milestones[milestone.id]
            if state in CLOSED_STATES:
                closed_task_count += count
            else:
                opened_task_count += count
            task_count_per_milestones[milestone.id] = opened_task_count, closed_task_count
        for milestone in unreached_milestones:
            opened_task_count, closed_task_count = task_count_per_milestones[milestone.id]
            milestone.can_be_marked_as_done = closed_task_count > 0 and not opened_task_count