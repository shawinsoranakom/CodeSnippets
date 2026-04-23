def test_responsible(self):
        """ Check that the responsible is correctly configured. """
        self.plan_onboarding.template_ids[0].write({
            'responsible_type': 'manager',
            'responsible_id': False,
        })
        self.plan_onboarding.write({
            'template_ids': [(0, 0, {
                'activity_type_id': self.activity_type_todo.id,
                'summary': 'Send feedback to the manager',
                'responsible_type': 'employee',
                'sequence': 30,
            })],
        })
        for employees in (self.employee_1, self.employee_1 + self.employee_2):
            # Happy case
            form = self._instantiate_activity_schedule_wizard(employees)
            form.plan_id = self.plan_onboarding
            expected_summary_lines = [
                ('Plan training', self.user_manager.id if len(employees) == 1 else False),
                ('Training', self.user_coach.id if len(employees) == 1 else False),
                ('Send feedback to the manager', employees.user_id.id if len(employees) == 1 else False),
            ]
            for summary_line, (expected_description, expected_responsible_id) in zip(
                form.plan_schedule_line_ids._records, expected_summary_lines, strict=True
            ):
                self.assertEqual(summary_line['line_description'], expected_description)
                self.assertEqual(summary_line['responsible_user_id'], expected_responsible_id)
            self.assertFalse(form.has_error)
            wizard = form.save()
            wizard.action_schedule_plan()
            for employee in employees:
                activities = self.get_last_activities(employee, 3)
                self.assertEqual(len(activities), 3)
                self.assertEqual(activities[0].user_id, self.user_manager)
                self.assertEqual(activities[1].user_id, self.user_coach)
                self.assertEqual(activities[2].user_id, employee.user_id)

            # Cases with errors
            self.employee_1.parent_id = False
            self.employee_1.coach_id = False
            form = self._instantiate_activity_schedule_wizard(employees)
            form.plan_id = self.plan_onboarding
            self.assertTrue(form.has_error)
            n_error = form.error.count('<li>')
            self.assertEqual(n_error, 2)
            self.assertIn(f'Manager of employee {self.employee_1.name} is not set.', form.error)
            self.assertIn(f'Coach of employee {self.employee_1.name} is not set.', form.error)
            with self.assertRaises(ValidationError):
                form.save()
            self.employee_1.parent_id = self.employee_manager
            self.employee_1.coach_id = self.employee_coach
            self.employee_coach.user_id = False
            self.employee_manager.user_id = False
            form = self._instantiate_activity_schedule_wizard(employees)
            form.plan_id = self.plan_onboarding
            self.assertTrue(form.has_warning)
            n_warning = form.warning.count('<li>')
            self.assertEqual(n_warning, 2 * len(employees))
            self.assertIn(f"The user of {self.employee_1.name}'s coach is not set.", form.warning)
            self.assertIn(f'The manager of {self.employee_1.name} should be linked to a user.', form.warning)
            if len(employees) > 1:
                self.assertIn(f"The user of {self.employee_2.name}'s coach is not set.", form.warning)
                self.assertIn(f'The manager of {self.employee_2.name} should be linked to a user.', form.warning)
            # should save without error, with coach
            form.save()
            self.employee_coach.user_id = self.user_coach
            self.employee_manager.user_id = self.user_manager