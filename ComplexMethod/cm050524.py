def default_get(self, fields):
        result = super().default_get(fields)
        if 'project_id' in fields and not result.get('project_id'):
            result['project_id'] = self.env.context.get('active_id')
        if result.get('project_id'):
            project = self.env['project.project'].browse(result['project_id'])
            if 'progress' in fields and not result.get('progress'):
                result['progress'] = project.last_update_id.progress
            if 'description' in fields and not result.get('description'):
                result['description'] = self._build_description(project)
            if 'status' in fields and not result.get('status'):
                # `to_define` is not an option for self.status, here we actually want to default to `on_track`
                # the goal of `to_define` is for a project to start without an actual status.
                result['status'] = project.last_update_status if project.last_update_status != 'to_define' else 'on_track'
        return result