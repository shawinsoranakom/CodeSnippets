def _compute_next_milestone_id(self):
        milestones_per_project_id = {
            project.id: milestones
            for project, milestones in self.env['project.milestone']._read_group(
                [('project_id', 'in', self.ids), ('is_reached', '=', False)],
                ['project_id'],
                ['id:recordset'],
            )
        }
        milestones = self.env['project.milestone'].concat(*milestones_per_project_id.values())
        task_read_group = self.env['project.task']._read_group(
            [('milestone_id', 'in', milestones.ids)],
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
        for project in self:
            milestones = milestones_per_project_id.get(project.id, self.env['project.milestone'])
            project.next_milestone_id = milestones[:1]
            milestone_deadline_exceeded = False
            milestone_marked_as_done = False
            for m in milestones:
                opened_task_count, closed_task_count = task_count_per_milestones[m.id]
                if (
                    not milestone_deadline_exceeded
                    and m.is_deadline_exceeded
                    and (opened_task_count > 0 or closed_task_count == 0)
                ):
                    milestone_deadline_exceeded = True
                    break
                if not milestone_marked_as_done and opened_task_count == 0 and closed_task_count > 0:
                    milestone_marked_as_done = True
            project.is_milestone_deadline_exceeded = milestone_deadline_exceeded
            project.can_mark_milestone_as_done = milestone_marked_as_done