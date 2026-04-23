def create(self, vals_list):
        # Prevent double project creation
        self = self.with_context(mail_create_nosubscribe=True)
        if any('label_tasks' in vals and not vals['label_tasks'] for vals in vals_list):
            task_label = _("Tasks")
            for vals in vals_list:
                if 'label_tasks' in vals and not vals['label_tasks']:
                    vals['label_tasks'] = task_label
        if self.env.user.has_group('project.group_project_stages'):
            if 'default_stage_id' in self.env.context:
                stage = self.env['project.project.stage'].browse(self.env.context['default_stage_id'])
                # The project's company_id must be the same as the stage's company_id
                if stage.company_id:
                    for vals in vals_list:
                        if vals.get('stage_id'):
                            continue
                        vals['company_id'] = stage.company_id.id
            else:
                companies_ids = [vals.get('company_id', False) for vals in vals_list] + [False]
                stages = self.env['project.project.stage'].search([('company_id', 'in', companies_ids)])
                for vals in vals_list:
                    if vals.get('stage_id'):
                        continue
                    # Pick the stage with the lowest sequence with no company or project's company
                    stage_domain = [False] if 'company_id' not in vals else [False, vals.get('company_id')]
                    stage = stages.filtered(lambda s: s.company_id.id in stage_domain)[:1]
                    vals['stage_id'] = stage.id

        for vals in vals_list:
            if vals.pop('is_favorite', False):
                vals['favorite_user_ids'] = [self.env.uid]
        projects = super().create(vals_list)
        return projects