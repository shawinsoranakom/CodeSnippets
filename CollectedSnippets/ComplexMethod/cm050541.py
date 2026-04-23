def _create_next_occurrences_values(self, recurrence_by_task):
        tasks = self.env['project.task'].concat(*recurrence_by_task.keys())
        list_create_values = []
        list_copy_data = tasks.with_context(copy_project=True, active_test=False).sudo().copy_data()
        list_fields_to_copy = tasks._read_format(self._get_recurring_fields_to_copy())
        list_fields_to_postpone = tasks._read_format(self._get_recurring_fields_to_postpone())

        for task, copy_data, fields_to_copy, fields_to_postpone in zip(
            tasks,
            list_copy_data,
            list_fields_to_copy,
            list_fields_to_postpone
        ):
            recurrence = recurrence_by_task[task]
            fields_to_postpone.pop('id', None)
            create_values = {
                'priority': '0',
                'stage_id': task.sudo().project_id.type_ids[0].id if task.sudo().project_id.type_ids else task.stage_id.id,
                'child_ids': [Command.create(vals) for vals in self._create_next_occurrences_values({child: recurrence for child in task.child_ids})]
            }
            create_values.update({
                field: value[0] if isinstance(value, tuple) else value
                for field, value in fields_to_copy.items()
            })
            create_values.update({
                field: value and value + recurrence._get_recurrence_delta()
                for field, value in fields_to_postpone.items()
            })
            copy_data.update(create_values)
            list_create_values.append(copy_data)

        return list_create_values