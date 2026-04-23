def get_grouped_tasks(pager_offset):
            tasks = Task_sudo.search(domain, order=order, limit=self._items_per_page, offset=pager_offset)
            request.session['my_project_tasks_history' if url.startswith('/my/projects') else 'my_tasks_history'] = tasks.ids[:100]

            tasks_project_allow_milestone = tasks.filtered(lambda t: t.allow_milestones)
            tasks_no_milestone = tasks - tasks_project_allow_milestone

            if groupby != 'none':
                if groupby == 'milestone_id':
                    grouped_tasks = [Task_sudo.concat(*g) for k, g in groupbyelem(tasks_project_allow_milestone, itemgetter(groupby))]

                    if not grouped_tasks:
                        if tasks_no_milestone:
                            grouped_tasks = [tasks_no_milestone]
                    else:
                        if grouped_tasks[len(grouped_tasks) - 1][0].milestone_id and tasks_no_milestone:
                            grouped_tasks.append(tasks_no_milestone)
                        else:
                            grouped_tasks[len(grouped_tasks) - 1] |= tasks_no_milestone

                else:
                    grouped_tasks = [Task_sudo.concat(*g) for k, g in groupbyelem(tasks, itemgetter(groupby))]
            else:
                grouped_tasks = [tasks] if tasks else []

            task_states = dict(Task_sudo._fields['state']._description_selection(request.env))
            if sortby == 'state':
                if groupby == 'none' and grouped_tasks:
                    grouped_tasks[0] = grouped_tasks[0].sorted(lambda tasks: task_states.get(tasks.state))
                else:
                    grouped_tasks.sort(key=lambda tasks: task_states.get(tasks[0].state))
            return grouped_tasks