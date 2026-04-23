def _get_milestone_values(self, project):
        Milestone = self.env['project.milestone']
        if not project.allow_milestones:
            return {
                'show_section': False,
                'list': [],
                'updated': [],
                'last_update_date': None,
                'created': []
            }
        list_milestones = Milestone.search(
            [('project_id', '=', project.id),
             '|', ('deadline', '<', fields.Date.context_today(self) + relativedelta(years=1)), ('deadline', '=', False)])._get_data_list()
        updated_milestones = self._get_last_updated_milestone(project)
        domain = Domain('project_id', '=', project.id)
        if project.last_update_id.create_date:
            domain &= Domain('create_date', '>', project.last_update_id.create_date)
        created_milestones = Milestone.search(domain)._get_data_list()
        return {
            'show_section': (list_milestones or updated_milestones or created_milestones) and True or False,
            'list': list_milestones,
            'updated': updated_milestones,
            'last_update_date': project.last_update_id.create_date or None,
            'created': created_milestones,
        }