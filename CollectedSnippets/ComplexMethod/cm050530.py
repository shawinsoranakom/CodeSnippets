def copy_data(self, default=None):
        default = dict(default or {})
        default.update({
            'depend_on_ids': False,
            'dependent_ids': False,
        })
        vals_list = super().copy_data(default=default)
        # filter only readable fields
        vals_list = [
            {
                k: v
                for k, v in vals.items()
                if self._has_field_access(self._fields[k], 'read')
            }
            for vals in vals_list
        ]

        active_users = self.env['res.users']
        has_default_users = 'user_ids' in default
        if not has_default_users:
            active_users = self.user_ids.filtered('active')
        milestone_mapping = self.env.context.get('milestone_mapping', {})
        for task, vals in zip(self, vals_list):

            if not default.get('stage_id'):
                vals['stage_id'] = task.stage_id.id
            if 'active' not in default and not task['active'] and not self.env.context.get('copy_project'):
                vals['active'] = True
            if not default.get('name'):
                vals['name'] = task.name if self.env.context.get('copy_project') or self.env.context.get('copy_from_template') else _("%s (copy)", task.name)
            if task.recurrence_id and not default.get('recurrence_id'):
                vals['recurrence_id'] = task.recurrence_id.copy().id
            if task.allow_milestones:
                vals['milestone_id'] = milestone_mapping.get(vals['milestone_id'], vals['milestone_id'])
            if not default.get('child_ids') and task.child_ids:
                whitelisted_fields = self._get_template_default_context_whitelist() if self.env.context.get('copy_from_template') else []
                default = {key: value for key, value in default.items() if key in whitelisted_fields}
                default['parent_id'] = False
                current_task = task
                if self.env.context.get('copy_from_template'):
                    current_task = current_task.with_context(active_test=True)
                child_ids = current_task.child_ids
                vals['child_ids'] = [Command.create(child_id.copy_data(default)[0]) for child_id in child_ids.filtered(lambda c: c.active)]
            if not has_default_users and vals['user_ids']:
                task_active_users = task.user_ids & active_users
                vals['user_ids'] = [Command.set(task_active_users.ids)]
            if self.env.context.get('copy_from_template') and not self.env.context.get('copy_from_project_template'):
                vals['is_template'] = False
            if self.env.context.get('copy_from_template'):
                for field in set(self._get_template_field_blacklist()) & set(vals.keys()):
                    del vals[field]
        return vals_list