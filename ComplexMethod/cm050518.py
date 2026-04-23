def test_planned_dates_consistency_for_project(self):
        """ This test ensures that a project can not have date start set,
            if its date end is False and that it can not have a date end
            set if its date start is False .
        """
        self.assertFalse(self.project_goats.date_start)
        self.assertFalse(self.project_goats.date)

        self.project_goats.write({'date_start': '2021-09-27', 'date': '2021-09-28'})
        self.assertEqual(fields.Date.to_string(self.project_goats.date_start), '2021-09-27', "The start date should be set.")
        self.assertEqual(fields.Date.to_string(self.project_goats.date), '2021-09-28', "The expiration date should be set.")

        self.project_goats.date_start = False
        self.assertFalse(fields.Date.to_string(self.project_goats.date_start), "The start date should be unset.")
        self.assertFalse(fields.Date.to_string(self.project_goats.date), "The expiration date should be unset as well.")

        self.project_goats.write({'date_start': '2021-09-27', 'date': '2021-09-28'})
        self.project_goats.date = False
        self.assertFalse(fields.Date.to_string(self.project_goats.date), "The expiration date should be unset.")
        self.assertFalse(fields.Date.to_string(self.project_goats.date_start), "The start date should be unset as well.")

        self.project_goats.write({'date_start': '2021-09-27'})
        self.assertFalse(fields.Date.to_string(self.project_goats.date_start), "The start date should be unset since expiration date if not set.")
        self.assertFalse(fields.Date.to_string(self.project_goats.date), "The expiration date should stay be unset.")

        self.project_goats.write({'date': '2021-09-28'})
        self.assertFalse(fields.Date.to_string(self.project_goats.date), "The expiration date should be unset since the start date if not set.")
        self.assertFalse(fields.Date.to_string(self.project_goats.date_start), "The start date should be unset.")

        self.project_pigs.write({'date_start': '2021-09-23', 'date': '2021-09-24'})

        # Case 1: one project has date range set and the other one has no date range set.
        projects = self.project_goats + self.project_pigs
        projects.write({'date_start': '2021-09-27', 'date': '2021-09-28'})
        for p in projects:
            self.assertEqual(fields.Date.to_string(p.date_start), '2021-09-27', f'The start date of {p.name} should be updated.')
            self.assertEqual(fields.Date.to_string(p.date), '2021-09-28', f'The expiration date of {p.name} should be updated.')
        self.project_goats.date_start = False
        projects.write({'date_start': '2021-09-30'})
        self.assertFalse(fields.Date.to_string(self.project_goats.date_start), 'The start date should not be updated')
        self.assertFalse(fields.Date.to_string(self.project_goats.date), 'The expiration date should not be updated')
        self.assertEqual(fields.Date.to_string(self.project_pigs.date_start), '2021-09-27', 'The start date should not be updated.')
        self.assertEqual(fields.Date.to_string(self.project_pigs.date), '2021-09-28', 'The expiration date should not be updated.')
        projects.write({'date_start': False})
        for p in projects:
            self.assertFalse(fields.Date.to_string(p.date_start), f'The start date of {p.name} should be set to False.')
            self.assertFalse(fields.Date.to_string(p.date), f'The expiration date of {p.name} should be set to False.')
        self.project_pigs.write({'date_start': '2021-09-27', 'date': '2021-09-28'})
        projects.write({'date': False})
        for p in projects:
            self.assertFalse(fields.Date.to_string(p.date_start), f'The start date of {p.name} should be set to False.')
            self.assertFalse(fields.Date.to_string(p.date), f'The expiration date of {p.name} should be set to False.')

        # Case 2: both projects have no date range set
        projects.write({'date_start': '2021-09-27'})
        for p in projects:
            self.assertFalse(fields.Date.to_string(p.date_start), f'The start date of {p.name} should not be updated.')
            self.assertFalse(fields.Date.to_string(p.date), f'The expiration date of {p.name} should not be updated.')
        projects.write({'date': '2021-09-28'})
        for p in projects:
            self.assertFalse(fields.Date.to_string(p.date_start), f'The start date of {p.name} should not be updated.')
            self.assertFalse(fields.Date.to_string(p.date), f'The expiration date of {p.name} should not be updated.')

        projects.write({'date_start': '2021-09-27', 'date': '2021-09-28'})
        for p in projects:
            self.assertEqual(fields.Date.to_string(p.date_start), '2021-09-27', f'The start date of {p.name} should be updated.')
            self.assertEqual(fields.Date.to_string(p.date), '2021-09-28', f'The expiration date of {p.name} should be updated.')

        # Case 3: both projects have a different date range set
        self.project_pigs.write({'date_start': '2021-09-23', 'date': '2021-09-30'})
        projects.write({'date_start': '2021-09-22'})
        self.assertEqual(fields.Date.to_string(self.project_goats.date_start), '2021-09-22', 'The start date should be updated.')
        self.assertEqual(fields.Date.to_string(self.project_goats.date), '2021-09-28', 'The expiration date should not be updated.')
        self.assertEqual(fields.Date.to_string(self.project_pigs.date_start), '2021-09-22', 'The start date should be updated.')
        self.assertEqual(fields.Date.to_string(self.project_pigs.date), '2021-09-30', 'The expiration date should not be updated.')
        projects.write({'date': '2021-09-29'})
        self.assertEqual(fields.Date.to_string(self.project_goats.date_start), '2021-09-22', 'The start date should not be updated.')
        self.assertEqual(fields.Date.to_string(self.project_goats.date), '2021-09-29', 'The expiration date should be updated.')
        self.assertEqual(fields.Date.to_string(self.project_pigs.date_start), '2021-09-22', 'The start date should not be updated.')
        self.assertEqual(fields.Date.to_string(self.project_pigs.date), '2021-09-29', 'The expiration date should be updated.')
        projects.write({'date_start': False})
        for p in projects:
            self.assertFalse(fields.Date.to_string(p.date_start), f'The start date of {p.name} should be set to False.')
            self.assertFalse(fields.Date.to_string(p.date), f'The expiration date of {p.name} should be set to False.')
        self.project_goats.write({'date_start': '2021-09-27', 'date': '2021-09-28'})
        self.project_pigs.write({'date_start': '2021-09-23', 'date': '2021-09-30'})
        projects.write({'date': False})
        for p in projects:
            self.assertFalse(fields.Date.to_string(p.date_start), f'The start date of {p.name} should be set to False.')
            self.assertFalse(fields.Date.to_string(p.date), f'The expiration date of {p.name} should be set to False.')
        self.project_goats.write({'date_start': '2021-09-27', 'date': '2021-09-28'})
        self.project_pigs.write({'date_start': '2021-09-23', 'date': '2021-09-30'})
        projects.write({'date_start': '2021-09-25', 'date': '2021-09-26'})
        for p in projects:
            self.assertEqual(fields.Date.to_string(p.date_start), '2021-09-25', f'The start date of {p.name} should be updated.')
            self.assertEqual(fields.Date.to_string(p.date), '2021-09-26', f'The expiration date of {p.name} should be updated.')