def _timesheet_create_project(self):
        project = super()._timesheet_create_project()
        # we can skip all the allocated hours calculation if allocated hours is already set on the template project
        if self.product_id.project_template_id.allocated_hours:
            project.write({
                'allocated_hours': self.product_id.project_template_id.allocated_hours,
                'allow_timesheets': True,
            })
            return project
        project_uom = self.company_id.project_time_mode_id
        uom_unit = self.env.ref('uom.product_uom_unit')
        uom_hour = self.env.ref('uom.product_uom_hour')

        # dict of inverse factors for each relevant UoM found in SO
        factor_per_id = {
            uom.id: uom.factor
            for uom in self.order_id.order_line.product_uom_id
        }
        # if sold as units, assume hours for time allocation
        factor_per_id[uom_unit.id] = uom_hour.factor

        allocated_hours = 0.0
        # method only called once per project, so also allocate hours for
        # all lines in SO that will share the same project
        for line in self.order_id.order_line:
            if line.is_service \
                    and line.product_id.service_tracking in ['task_in_project', 'project_only'] \
                    and line.product_id.project_template_id == self.product_id.project_template_id \
                    and line.product_uom_id.id in factor_per_id:
                uom_factor = factor_per_id[line.product_uom_id.id] / project_uom.factor
                allocated_hours += line.product_uom_qty * uom_factor

        project.write({
            'allocated_hours': allocated_hours,
            'allow_timesheets': True,
        })
        return project