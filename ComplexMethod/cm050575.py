def _compute_name(self):
        for resource in self:
            to_update = not resource.name or resource.name == _("Resource")
            if to_update:
                new_name = _("Resource")
                if resource.resource_type == 'file' and (resource.data or resource.file_name):
                    new_name = resource.file_name
                elif resource.resource_type == 'url':
                    new_name = resource.link
                resource.name = new_name