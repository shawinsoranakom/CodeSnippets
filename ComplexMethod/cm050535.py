def _mail_get_message_subtypes(self):
        res = super()._mail_get_message_subtypes()
        if not self.stage_id.rating_active:
            res -= self.env.ref('project.mt_task_rating')
        if len(self) == 1:
            waiting_subtype = self.env.ref('project.mt_task_waiting')
            if ((self.project_id and not self.project_id.allow_task_dependencies)\
                or (not self.project_id and not self.env.user.has_group('project.group_project_task_dependencies')))\
                and waiting_subtype in res:
                res -= waiting_subtype
        return res