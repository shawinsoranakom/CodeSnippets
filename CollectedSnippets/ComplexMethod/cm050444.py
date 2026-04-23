def test_hierarchy_read(self):
        HrEmployee = self.env['hr.employee']
        employees = self.employee_georges + self.employee_paul + self.employee_pierre
        specification = {'id': {}}

        def get_expected_dict(employee):
            return {
                'id': employee.id,
                'parent_id':
                    employee.parent_id.id
                    and {'id': employee.parent_id.id, 'display_name': employee.parent_id.display_name},
            }

        result = HrEmployee.hierarchy_read([('id', 'in', employees.ids)], specification, 'parent_id')
        for emp in employees:
            self.assertIn(get_expected_dict(emp), result)

        self.employee_georges.parent_id = self.employee_paul
        self.employee_pierre.parent_id = self.employee_paul
        result = HrEmployee.hierarchy_read([('id', 'in', employees.ids)], specification, 'parent_id')
        self.assertEqual(len(result), 3)
        for emp in employees:
            emp_dict = get_expected_dict(emp)
            if not emp.parent_id:
                emp_dict['__child_ids__'] = [self.employee_georges.id, self.employee_pierre.id]
            self.assertIn(emp_dict, result)

        employee_count = HrEmployee.search_count([('id', 'not in', employees.ids), ('parent_id', '=', False)])
        result = HrEmployee.hierarchy_read([('parent_id', '=', False)], specification, 'parent_id')
        self.assertEqual(len(result), 1 + employee_count)
        for employee_dict in result:
            self.assertFalse(employee_dict['parent_id'], "Each employee in the result should not have any parent set.")
        expected_emp_dict = get_expected_dict(self.employee_paul)
        self.assertIn(
            {**expected_emp_dict, '__child_ids__': [self.employee_georges.id, self.employee_pierre.id]},
            result
        )

        result = HrEmployee.hierarchy_read([('id', '=', self.employee_paul.id)], specification, 'parent_id')
        self.assertEqual(len(result), 3)

        for emp in employees:
            self.assertIn(get_expected_dict(emp), result)

        result = HrEmployee.hierarchy_read([('id', '=', self.employee_georges.id)], specification, 'parent_id')
        self.assertEqual(len(result), 3)
        for emp in employees:
            self.assertIn(get_expected_dict(emp), result)

        self.employee_pierre.parent_id = self.employee_georges
        result = HrEmployee.hierarchy_read([('id', '=', self.employee_georges.id)], specification, 'parent_id')
        self.assertEqual(len(result), 3)
        for emp in employees:
            self.assertIn(get_expected_dict(emp), result)

        result = HrEmployee.hierarchy_read([('id', '=', self.employee_pierre.id)], specification, 'parent_id')
        self.assertEqual(len(result), 2)
        self.assertIn(get_expected_dict(self.employee_pierre), result)
        self.assertIn(get_expected_dict(self.employee_georges), result)