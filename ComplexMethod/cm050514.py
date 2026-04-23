def _task_get_page_view_values(self, task, access_token, **kwargs):
        project = kwargs.get('project')
        if project:
            project_accessible = True
            page_name = 'project_task'
            history = 'my_project_tasks_history'
        else:
            page_name = 'task'
            history = 'my_tasks_history'
            try:
                project_accessible = bool(task.project_id.id and self._document_check_access('project.project', task.project_id.id))
            except (AccessError, MissingError):
                project_accessible = False
        values = {
            'page_name': page_name,
            'priority_labels': dict(task._fields['priority']._description_selection(request.env)),
            'task': task,
            'user': request.env.user,
            'project_accessible': project_accessible,
            'task_link_section': [],
            'preview_object': task,
        }

        values = self._get_page_view_values(task, access_token, values, history, False, **kwargs)
        if project:
            values['project_id'] = project.id
            history = request.session.get('my_project_tasks_history', [])
            try:
                current_task_index = history.index(task.id)
            except ValueError:
                return values

            total_task = len(history)
            task_url = f"{task.project_id.access_url}/task/%s?model=project.project&res_id={values['user'].id}&access_token={access_token}"

            values['prev_record'] = current_task_index != 0 and task_url % history[current_task_index - 1]
            values['next_record'] = current_task_index < total_task - 1 and task_url % history[current_task_index + 1]

        return values