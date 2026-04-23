def copy(self, default=None):
        default = dict(default or {})
        # Since we dont want to copy the milestones if the original project has the feature disabled, we set the milestones to False by default.
        default['milestone_ids'] = False
        copy_context = dict(
             self.env.context,
             mail_auto_subscribe_no_notify=True,
             mail_create_nosubscribe=True,
         )
        copy_context.pop("default_stage_id", None)
        new_projects = super(ProjectProject, self.with_context(copy_context)).copy(default=default)
        if 'milestone_mapping' not in self.env.context:
            self = self.with_context(milestone_mapping={})
        for old_project, new_project in zip(self, new_projects):
            for follower in old_project.message_follower_ids:
                new_project.message_subscribe(partner_ids=follower.partner_id.ids, subtype_ids=follower.subtype_ids.ids)
            if old_project.allow_milestones:
                new_project.milestone_ids = self.milestone_ids.copy().ids
            if 'tasks' not in default:
                old_project.map_tasks(new_project.id)
            if not old_project.active:
                new_project.with_context(active_test=False).tasks.active = True
        # Copy the shared embedded actions and config in the new projects
        shared_embedded_actions_mapping = self._copy_shared_embedded_actions(new_projects)
        self._copy_embedded_actions_config(new_projects, shared_embedded_actions_mapping)
        return new_projects