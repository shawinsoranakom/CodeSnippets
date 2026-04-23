def default_get(self, fields):
        # The project share action could be called in `project.collaborator`
        # and so we have to check the active_model and active_id to use
        # the right project.
        active_model = self.env.context.get('active_model', '')
        active_id = self.env.context.get('active_id', False)
        if active_model == 'project.collaborator':
            active_model = 'project.project'
            active_id = self.env.context.get('default_project_id', False)
        result = super(ProjectShareWizard, self.with_context(active_model=active_model, active_id=active_id)).default_get(fields)
        if result['res_model'] and result['res_id']:
            project = self.env[result['res_model']].browse(result['res_id'])
            collaborator_vals_list = []
            collaborator_ids = []
            for collaborator in project.collaborator_ids:
                collaborator_ids.append(collaborator.partner_id.id)
                collaborator_vals_list.append({
                    'partner_id': collaborator.partner_id.id,
                    'partner_name': collaborator.partner_id.display_name,
                    'access_mode': 'edit_limited' if collaborator.limited_access else 'edit',
                })
            for follower in project.message_partner_ids:
                if follower.partner_share and follower.id not in collaborator_ids:
                    collaborator_vals_list.append({
                        'partner_id': follower.id,
                        'partner_name': follower.display_name,
                        'access_mode': 'read',
                    })
            if collaborator_vals_list:
                collaborator_vals_list.sort(key=operator.itemgetter('partner_name'))
                result['collaborator_ids'] = [
                    Command.create({'partner_id': collaborator['partner_id'], 'access_mode': collaborator['access_mode'], 'send_invitation': False})
                    for collaborator in collaborator_vals_list
                ]
        return result