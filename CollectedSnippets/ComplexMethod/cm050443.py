def get_org_chart(self, employee_id, new_parent_id=None, **kw):
        employee = self._get_employee(employee_id, **kw)
        new_parent = self._get_employee(new_parent_id, **kw).sudo()
        if not employee:  # to check
            return {
                'managers': [],
                'children': [],
            }

        # compute employee data for org chart
        ancestors, current = request.env['hr.employee.public'].sudo(), employee.sudo()
        current_parent = new_parent if new_parent_id is not None else current.parent_id
        max_level = (kw.get('context')['max_level'] or self._managers_level) + 1
        while current_parent and current != current_parent and employee.sudo() != current_parent and len(ancestors) < max_level:
            current = current_parent
            current_parent = current.parent_id if current != employee or not new_parent else new_parent
            if current_parent in ancestors:
                break
            ancestors += current

        values = dict(
            self=self._prepare_employee_data(employee),
            managers=[
                self._prepare_employee_data(ancestor)
                for idx, ancestor in enumerate(ancestors)
                if idx < max_level - 1
            ],
            managers_more=len(ancestors) > self._managers_level,
            children=[self._prepare_employee_data(child) for child in employee.child_ids if child != employee],
        )
        values['managers'].reverse()
        return values