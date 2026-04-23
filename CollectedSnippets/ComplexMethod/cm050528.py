def _compute_depend_on_count(self):
        tasks_with_dependency = self.filtered('allow_task_dependencies')
        tasks_without_dependency = self - tasks_with_dependency
        tasks_without_dependency.depend_on_count = 0
        tasks_without_dependency.closed_depend_on_count = 0
        if not any(self._ids):
            for task in self:
                task.depend_on_count = len(task.depend_on_ids)
                task.closed_depend_on_count = len(task.depend_on_ids.filtered(lambda r: r.state in CLOSED_STATES))
            return
        if tasks_with_dependency:
            # need the sudo for project sharing
            total_and_closed_depend_on_count = {
                dependent_on.id: (count, sum(s in CLOSED_STATES for s in states))
                for dependent_on, states, count in self.env['project.task']._read_group(
                    [('dependent_ids', 'in', tasks_with_dependency.ids)],
                    ['dependent_ids'],
                    ['state:array_agg', '__count'],
                )
            }
            for task in tasks_with_dependency:
                task.depend_on_count, task.closed_depend_on_count = total_and_closed_depend_on_count.get(task._origin.id or task.id, (0, 0))