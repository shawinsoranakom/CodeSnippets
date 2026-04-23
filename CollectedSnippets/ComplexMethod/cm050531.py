def default_get(self, fields):
        vals = super().default_get(fields)

        if project_id := self.env.context.get('default_create_in_project_id'):
            vals['project_id'] = project_id

        # prevent creating new task in the waiting state
        if 'state' in fields and vals.get('state') == '04_waiting_normal':
            vals['state'] = '01_in_progress'

        if 'repeat_until' in fields:
            vals['repeat_until'] = Date.today() + timedelta(days=7)

        if 'partner_id' in vals and not vals['partner_id']:
            # if the default_partner_id=False or no default_partner_id then we search the partner based on the project and parent
            project_id = vals.get('project_id')
            parent_id = vals.get('parent_id', self.env.context.get('default_parent_id'))
            if project_id or parent_id:
                partner_id = self._get_default_partner_id(
                    project_id and self.env['project.project'].browse(project_id),
                    parent_id and self.env['project.task'].browse(parent_id)
                )
                if partner_id:
                    vals['partner_id'] = partner_id
        project_id = vals.get('project_id', self.env.context.get('default_project_id'))
        if project_id:
            project = self.env['project.project'].browse(project_id)
            if 'company_id' in fields and 'default_project_id' not in self.env.context:
                vals['company_id'] = project.sudo().company_id.id
        elif 'default_user_ids' not in self.env.context and 'user_ids' in fields:
            user_ids = vals.get('user_ids', [])
            user_ids.append(Command.link(self.env.user.id))
            vals['user_ids'] = user_ids

        parent_id = vals.get('parent_id', self.env.context.get('default_parent_id'))
        if parent_id:
            parent = self.env['project.task'].browse(parent_id)
            if not vals.get('tag_ids'):
                vals['tag_ids'] = parent.tag_ids

        return vals