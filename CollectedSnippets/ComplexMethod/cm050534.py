def write(self, vals):
        self.check_access('write')
        if len(self) == 1:
            handle_history_divergence(self, 'description', vals)
        partner_ids = []

        # Some values are determined by this override and must be written as
        # sudo for portal users, because they do not have access to these
        # fields. Other values must not be written as sudo.
        additional_vals = {}
        if self.env.user._is_portal() and not self.env.su:
            self._ensure_fields_write(vals, defaults=False)

        if 'milestone_id' in vals:
            # WARNING: has to be done after 'project_id' vals is written on subtasks
            milestone = self.env['project.milestone'].browse(vals['milestone_id'])

            # 1. Task for which the milestone is unvalid -> milestone_id is reset
            if 'project_id' not in vals:
                unvalid_milestone_tasks = self.filtered(lambda task: task.project_id != milestone.project_id) if vals['milestone_id'] else self.env['project.task']
            else:
                unvalid_milestone_tasks = self if not vals['milestone_id'] or milestone.project_id.id != vals['project_id'] else self.env['project.task']
            valid_milestone_tasks = self - unvalid_milestone_tasks
            if unvalid_milestone_tasks:
                unvalid_milestone_tasks.sudo().write({'milestone_id': False})
                if valid_milestone_tasks:
                    valid_milestone_tasks.sudo().write({'milestone_id': vals['milestone_id']})
                del vals['milestone_id']

            # 2. Parent's milestone is set to subtask with no milestone recursively
            subtasks_to_update = valid_milestone_tasks.child_ids.filtered(
                lambda task: (task not in self and
                              not task.milestone_id and
                              task.project_id == milestone.project_id and
                              task.state not in CLOSED_STATES))

            # 3. If parent and child task share the same milestone, child task's milestone is updated when the parent one is changed
            # No need to check if state is changed in vals as it won't affect the subtasks selected for update
            if 'project_id' not in vals:
                subtasks_to_update |= valid_milestone_tasks.child_ids.filtered(
                    lambda task: (task not in self and
                                  task.milestone_id == task.parent_id.milestone_id and
                                  task.state not in CLOSED_STATES))
            else:
                subtasks_to_update |= valid_milestone_tasks.child_ids.filtered(
                    lambda task: (task not in self and
                                  (not task.display_in_project or task.project_id.id == vals['project_id']) and
                                  task.milestone_id == task.parent_id.milestone_id and
                                  task.state not in CLOSED_STATES))
            if subtasks_to_update:
                subtasks_to_update.sudo().write({'milestone_id': vals['milestone_id']})

        if vals.get('parent_id') in self.ids:
            raise UserError(_("Sorry. You can't set a task as its parent task."))

        # stage change: update date_last_stage_update
        now = fields.Datetime.now()
        if 'stage_id' in vals:
            if not 'project_id' in vals and self.filtered(lambda t: not t.project_id):
                raise UserError(_('You can only set a personal stage on a private task.'))

            additional_vals.update(self.update_date_end(vals['stage_id']))
            additional_vals['date_last_stage_update'] = now
        task_ids_without_user_set = set()
        if 'user_ids' in vals and 'date_assign' not in vals:
            # prepare update of date_assign after super call
            task_ids_without_user_set = {task.id for task in self if not task.user_ids}

        # recurrence fields
        rec_fields = vals.keys() & self._get_recurrence_fields()
        if rec_fields:
            rec_values = {rec_field: vals[rec_field] for rec_field in rec_fields}
            for task in self:
                if task.recurrence_id:
                    task.recurrence_id.write(rec_values)
                elif vals.get('recurring_task'):
                    recurrence = self.env['project.task.recurrence'].create(rec_values)
                    task.recurrence_id = recurrence.id

        if not vals.get('recurring_task', True) and self.recurrence_id:
            tasks_in_recurrence = self.recurrence_id.task_ids
            self.recurrence_id.unlink()
            tasks_in_recurrence.write({'recurring_task': False})

        # Track user_ids to send assignment notifications
        old_user_ids = {t: t.user_ids for t in self.sudo()}

        if "personal_stage_type_id" in vals and not vals['personal_stage_type_id']:
            del vals['personal_stage_type_id']

        # sends an email to the 'Task Creation' subtype subscribers
        # When project_id is changed
        project_link_per_task_id = {}
        if vals.get('project_id'):
            project = self.env['project.project'].browse(vals.get('project_id'))
            notification_subtype_id = self.env['ir.model.data']._xmlid_to_res_id('project.mt_project_task_new')
            partner_ids = project.message_follower_ids.filtered(lambda follower: notification_subtype_id in follower.subtype_ids.ids).partner_id.ids
            if partner_ids:
                link_per_project_id = {}
                for task in self:
                    if task.project_id:
                        project_link = link_per_project_id.get(task.project_id.id)
                        if not project_link:
                            project_link = link_per_project_id[task.project_id.id] = task.project_id._get_html_link(title=task.project_id.display_name)
                        project_link_per_task_id[task.id] = project_link
        if vals.get('parent_id') is False:
            additional_vals['display_in_project'] = True
        if 'description' in vals:
            # the portal user cannot access to html_field_history and so it would be
            # better to write in sudo for description field to avoid giving access to html_field_history
            additional_vals['description'] = vals.pop('description')

            # write changes
        if self.env.su or not self.env.user._is_portal():
            vals.update(additional_vals)
        elif additional_vals:
            super(ProjectTask, self.sudo()).write(additional_vals)
        result = super().write(vals)

        if 'user_ids' in vals:
            self._populate_missing_personal_stages()

        # user_ids change: update date_assign
        if 'user_ids' in vals:
            for task in self.sudo():
                if not task.user_ids and task.date_assign:
                    task.date_assign = False
                elif 'date_assign' not in vals and task.id in task_ids_without_user_set:
                    task.date_assign = now

        # rating on stage
        if 'stage_id' in vals and vals.get('stage_id'):
            self.sudo().filtered(lambda x: x.stage_id.rating_active and x.stage_id.rating_status == 'stage')._send_task_rating_mail(force_send=True)

        if 'state' in vals:
            # specific use case: when the blocked task goes from 'forced' done state to a not closed state, we fix the state back to waiting
            for task in self.sudo():
                if task.allow_task_dependencies:
                    if task.is_blocked_by_dependences() and vals['state'] not in CLOSED_STATES and vals['state'] != '04_waiting_normal':
                        task.state = '04_waiting_normal'
                task.date_last_stage_update = now
        elif 'project_id' in vals:
            self.filtered(lambda t: t.state != '04_waiting_normal').state = '01_in_progress'

        # Do not recompute the state when changing the parent (to avoid resetting the state)
        if 'parent_id' in vals:
            self.env.remove_to_compute(self._fields['state'], self)

        self._task_message_auto_subscribe_notify({task: task.user_ids - old_user_ids[task] - self.env.user for task in self})

        if partner_ids:
            for task in self:
                project_link = project_link_per_task_id.get(task.id)
                if project_link:
                    body = _(
                        'Task Transferred from Project %(source_project)s to %(destination_project)s',
                        source_project=project_link,
                        destination_project=task.project_id._get_html_link(title=task.project_id.display_name),
                    )
                else:
                    body = _('Task Converted from To-Do')
                task.message_notify(
                    body=body,
                    partner_ids=partner_ids,
                    email_layout_xmlid='mail.mail_notification_layout',
                    notify_author_mention=False,
               )
        return result