def _get_stat_buttons(self):
        self.ensure_one()
        closed_task_count = self.task_count - self.open_task_count
        if self.task_count:
            number = self.env._(
                "%(closed_task_count)s / %(task_count)s (%(closed_rate)s%%)",
                closed_task_count=closed_task_count,
                task_count=self.task_count,
                closed_rate=round(100 * closed_task_count / self.task_count),
            )
        else:
            number = self.env._(
                "%(closed_task_count)s / %(task_count)s",
                closed_task_count=closed_task_count,
                task_count=self.task_count,
            )
        buttons = [{
            'icon': 'check',
            'text': self.label_tasks,
            'number': number,
            'action_type': 'object',
            'action': 'action_view_tasks',
            'show': True,
            'sequence': 1,
        }]
        if self.rating_count != 0:
            if self.rating_avg >= rating_data.RATING_AVG_TOP:
                icon = 'smile-o text-success'
            elif self.rating_avg >= rating_data.RATING_AVG_OK:
                icon = 'meh-o text-warning'
            else:
                icon = 'frown-o text-danger'
            buttons.append({
                'icon': icon,
                'text': self.env._('Average Rating'),
                'number': f'{int(self.rating_avg) if self.rating_avg.is_integer() else round(self.rating_avg, 1)} / 5',
                'action_type': 'object',
                'action': 'action_view_all_rating',
                'show': self.show_ratings,
                'sequence': 15,
            })
        if self.env.user.has_group('project.group_project_user'):
            buttons.append({
                'icon': 'area-chart',
                'text': self.env._('Burndown Chart'),
                'action_type': 'action',
                'action': 'project.action_project_task_burndown_chart_report',
                'additional_context': json.dumps({
                    'active_id': self.id,
                    'stage_name_and_sequence_per_id': {
                        stage.id: {
                            'sequence': stage.sequence,
                            'name': stage.name
                        } for stage in self.type_ids
                    },
                }),
                'show': True,
                'sequence': 60,
            })
        return buttons