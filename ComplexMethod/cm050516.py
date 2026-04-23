def _prepare_tasks_values(self, page, date_begin, date_end, sortby, search, search_in, groupby, url="/my/tasks", domain=None, su=False, project=False):
        values = self._prepare_portal_layout_values()

        Task = request.env['project.task']

        domain = Domain.AND([domain or [], [('has_template_ancestor', '=', False)]])
        if not su and Task.has_access('read'):
            domain &= Domain(request.env['ir.rule']._compute_domain(Task._name, 'read'))
        Task_sudo = Task.sudo()
        milestone_domain = domain & Domain('allow_milestones', '=', True) & Domain('milestone_id', '!=', False)
        milestones_allowed = Task_sudo.search_count(milestone_domain, limit=1) == 1
        searchbar_sortings = dict(sorted(self._task_get_searchbar_sortings(milestones_allowed, project).items(),
                                         key=lambda item: item[1]["sequence"]))
        searchbar_inputs = dict(sorted(self._task_get_searchbar_inputs(milestones_allowed, project).items(), key=lambda item: item[1]['sequence']))
        searchbar_groupby = dict(sorted(self._task_get_searchbar_groupby(milestones_allowed, project).items(), key=lambda item: item[1]['sequence']))

        # default sort by value
        if not sortby or (sortby == 'milestone_id' and not milestones_allowed):
            sortby = next(iter(searchbar_sortings))

        # default group by value
        if not groupby or (groupby == 'milestone_id' and not milestones_allowed):
            groupby = 'project_id'

        if date_begin and date_end:
            domain &= Domain('create_date', '>', date_begin) & Domain('create_date', '<=', date_end)

        # search reset if needed
        if not milestones_allowed and search_in == 'milestone_id':
            search_in = 'all'
        # search
        if search and search_in:
            domain &= Domain(self._task_get_search_domain(search_in, search, milestones_allowed, project))

        # content according to pager and archive selected
        if groupby == 'none':
            group_field = None
        elif groupby == 'priority':
            group_field = 'priority desc'
        else:
            group_field = groupby
        order = '%s, %s' % (group_field, sortby) if group_field else sortby

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

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'grouped_tasks': get_grouped_tasks,
            'allow_milestone': milestones_allowed,
            'multiple_projects': True,
            'priority_labels': dict(Task_sudo._fields['priority']._description_selection(request.env)),
            'page_name': 'task',
            'default_url': url,
            'task_url': 'tasks',
            'pager': {
                "url": url,
                "url_args": {'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'groupby': groupby, 'search_in': search_in, 'search': search},
                "total": Task_sudo.search_count(domain),
                "page": page,
                "step": self._items_per_page
            },
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
        })
        return values