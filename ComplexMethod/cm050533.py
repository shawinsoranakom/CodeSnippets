def create(self, vals_list):
        # Some values are determined by this override and must be written as
        # sudo for portal users, because they do not have access to these
        # fields. Other values must not be written as sudo.
        additional_vals_list = [{} for _ in vals_list]

        new_context = dict(self.env.context)
        default_personal_stage = new_context.pop('default_personal_stage_type_ids', False)
        default_project_id = new_context.pop('default_project_id', False)
        if not default_project_id:
            parent_task = self.browse({parent_id for vals in vals_list if (parent_id := vals.get('parent_id'))})
            if len(parent_task) == 1:
                default_project_id = parent_task.sudo().project_id.id
        # (portal) users that don't have write access can still create a task
        # in the project that will be checked using record rules
        new_context["default_create_in_project_id"] = default_project_id
        if not self._has_field_access(self._fields['user_ids'], 'write'):
            # remove user_ids if we have no access to it
            new_context.pop('default_user_ids', False)
        self_ctx = self.with_context(new_context)

        self_ctx.browse().check_access('create')
        default_stage = dict()
        for vals, additional_vals in zip(vals_list, additional_vals_list):
            project_id = vals.get('project_id') or default_project_id

            if vals.get('user_ids'):
                additional_vals['date_assign'] = fields.Datetime.now()
                if not (vals.get('parent_id') or project_id):
                    user_ids = self_ctx._fields['user_ids'].convert_to_cache(vals.get('user_ids', []), self_ctx.env['project.task'])
                    if self_ctx.env.user.id not in list(user_ids) + [SUPERUSER_ID]:
                        additional_vals['user_ids'] = [Command.set(list(user_ids) + [self_ctx.env.user.id])]
            if default_personal_stage and 'personal_stage_type_id' not in vals:
                additional_vals['personal_stage_type_id'] = default_personal_stage[0]
            if not vals.get('name') and vals.get('display_name'):
                vals['name'] = vals['display_name']

            if self_ctx.env.user._is_portal() and not self_ctx.env.su:
                self_ctx._ensure_fields_write(vals, defaults=True)

            if project_id and not "company_id" in vals:
                additional_vals["company_id"] = self_ctx.env["project.project"].browse(
                    project_id
                ).company_id.id
            if not project_id and ("stage_id" in vals or self_ctx.env.context.get('default_stage_id')):
                vals["stage_id"] = False

            if project_id and "stage_id" not in vals:
                # 1) Allows keeping the batch creation of tasks
                # 2) Ensure the defaults are correct (and computed once by project),
                # by using default get (instead of _get_default_stage_id or _stage_find),
                if project_id not in default_stage:
                    default_stage[project_id] = self_ctx.with_context(
                        default_project_id=project_id
                    ).default_get(['stage_id']).get('stage_id')
                vals["stage_id"] = default_stage[project_id]

            # Stage change: Update date_end if folded stage and date_last_stage_update
            if vals.get('stage_id'):
                additional_vals.update(self_ctx.update_date_end(vals['stage_id']))
                additional_vals['date_last_stage_update'] = fields.Datetime.now()
            # recurrence
            rec_fields = vals.keys() & self_ctx._get_recurrence_fields()
            if rec_fields and vals.get('recurring_task') is True:
                rec_values = {rec_field: vals[rec_field] for rec_field in rec_fields}
                recurrence = self_ctx.env['project.task.recurrence'].create(rec_values)
                vals['recurrence_id'] = recurrence.id

        # create the task, write computed inaccessible fields in sudo
        for vals, computed_vals in zip(vals_list, additional_vals_list):
            for field_name in list(computed_vals):
                if self_ctx._has_field_access(self_ctx._fields[field_name], 'write'):
                    vals[field_name] = computed_vals.pop(field_name)
        # no track when the portal user create a task to avoid using during tracking
        # process since the portal does not have access to tracking models
        tasks = super(ProjectTask, self_ctx.with_context(mail_create_nosubscribe=True, mail_notrack=not self_ctx.env.su and self_ctx.env.user._is_portal())).create(vals_list)
        for task, computed_vals in zip(tasks.sudo(), additional_vals_list):
            if computed_vals:
                task.write(computed_vals)
        tasks.sudo()._populate_missing_personal_stages()
        self_ctx._task_message_auto_subscribe_notify({task: task.user_ids - self_ctx.env.user for task in tasks})

        current_partner = self_ctx.env.user.partner_id

        all_partner_emails = []
        for task in tasks.sudo():
            all_partner_emails += tools.email_normalize_all(task.email_cc)
        partners = self_ctx.env['res.partner'].search([('email', 'in', all_partner_emails)])
        partner_per_email = {
            partner.email: partner
            for partner in partners
            if not all(u.share for u in partner.user_ids)
        }
        if tasks.project_id:
            tasks.sudo()._set_stage_on_project_from_task()
        for task in tasks.sudo():
            if task.project_id.privacy_visibility in ['invited_users', 'portal']:
                task._portal_ensure_token()
            for follower in task.parent_id.message_follower_ids:
                task.message_subscribe(follower.partner_id.ids, follower.subtype_ids.ids)
            if current_partner not in task.message_partner_ids:
                task.message_subscribe(current_partner.ids)
            if task.email_cc:
                partners_with_internal_user = self_ctx.env['res.partner']
                for email in tools.email_normalize_all(task.email_cc):
                    new_partner = partner_per_email.get(email)
                    if new_partner:
                        partners_with_internal_user |= new_partner
                if not partners_with_internal_user:
                    continue
                task._send_email_notify_to_cc(partners_with_internal_user)
                task.message_subscribe(partners_with_internal_user.ids)
        return tasks