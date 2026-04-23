def write(self, vals):
        if 'active' in vals and not vals['active']:
            self.env['project.task'].search([('stage_id', 'in', self.ids)]).write({'active': False})
        # Hide/Show task rating template when customer rating feature is disabled/enabled
        if 'rating_active' in vals:
            rating_active = vals['rating_active']
            task_types = self.env['project.task.type'].search([('rating_active', '=', True)])
            if (not task_types and rating_active) or (task_types and task_types <= self and not rating_active):
                mt_project_task_rating = self.env.ref('project.mt_project_task_rating')
                mt_project_task_rating.hidden = not rating_active
                mt_project_task_rating.default = rating_active
                self.env.ref('project.mt_task_rating').hidden = not rating_active
                self.env.ref('project.rating_project_request_email_template').active = rating_active
        return super().write(vals)