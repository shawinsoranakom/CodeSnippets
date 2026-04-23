def _check_project_and_template(self):
        """ NOTE 'service_tracking' should be in decorator parameters but since ORM check constraints twice (one after setting
            stored fields, one after setting non stored field), the error is raised when company-dependent fields are not set.
            So, this constraints does cover all cases and inconsistent can still be recorded until the ORM change its behavior.
        """
        for product in self:
            if product.service_tracking == 'no' and (product.project_id or product.project_template_id):
                raise ValidationError(_('The product %s should not have a project nor a project template since it will not generate project.', product.name))
            elif product.service_tracking == 'task_global_project' and product.project_template_id:
                raise ValidationError(_('The product %s should not have a project template since it will generate a task in a global project.', product.name))
            elif product.service_tracking in ['task_in_project', 'project_only'] and product.project_id:
                raise ValidationError(_('The product %s should not have a global project since it will generate a project.', product.name))