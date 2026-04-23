def action_create_from_template(self, values=None, role_to_users_mapping=None):
        self.ensure_one()
        values = values or {}

        if self.date_start and self.date:
            if not values.get("date_start"):
                values["date_start"] = fields.Date.today()
            if not values.get("date"):
                values["date"] = values["date_start"] + (self.date - self.date_start)

        default = {
            key.removeprefix('default_'): value
            for key, value in self.env.context.items()
            if key.startswith('default_') and key.removeprefix('default_') in self._get_template_default_context_whitelist()
        } | values
        project = self.with_context(copy_from_template=True, copy_from_project_template=True).copy(default=default)
        project.message_post(body=self.env._("Project created from template %(name)s.", name=self.name))

        # Tasks dispatching using project roles
        if role_to_users_mapping and (mapping := role_to_users_mapping.filtered(lambda entry: entry.user_ids)):
            for new_task in project.task_ids:
                for entry in mapping:
                    if entry.role_id in new_task.role_ids:
                        new_task.user_ids |= entry.user_ids

        project.task_ids.role_ids = False
        return project