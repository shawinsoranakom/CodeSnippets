def _task_get_search_domain(self, search_in, search, milestones_allowed, project):
        if not search_in or search_in == 'name':
            return ['|', ('name', 'ilike', search), ('id', 'ilike', search)]
        elif search_in == 'user_ids':
            user_ids = request.env['res.users'].sudo().search([('name', 'ilike', search)])
            return [('user_ids', 'in', user_ids.ids)]
        elif search_in == 'priority':
            priority_selections = request.env['ir.model.fields.selection'].sudo().search([
                ('field_id.model', '=', 'project.task'),
                ('field_id.name', '=', 'priority'),
                ('name', 'ilike', search),
            ])
            if priority_selections:
                return [('priority', 'in', priority_selections.mapped('value'))]
            return Domain.FALSE
        elif search_in == 'status':
            state_selections = request.env['ir.model.fields.selection'].sudo().search([
                ('field_id.model', '=', 'project.task'),
                ('field_id.name', '=', 'state'),
                ('name', 'ilike', search),
            ])
            if state_selections:
                return [('state', 'in', state_selections.mapped('value'))]
            return Domain.FALSE
        elif search_in in self._task_get_searchbar_inputs(milestones_allowed, project):
            return [(search_in, 'ilike', search)]
        else:
            return ['|', ('name', 'ilike', search), ('id', 'ilike', search)]