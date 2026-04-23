def test_systray_activities_multi_company(self):
        """ Explicitly check MC support, as well as allowed_company_ids, that
        limits visible records in a given session, should impact systray activities. """
        self.user_employee.write({'company_ids': [(4, self.company_2.id)]})

        self.authenticate(self.user_employee.login, self.user_employee.login)
        with freeze_time(self.dt_reference):
            groups_data = self.make_jsonrpc_request("/mail/data", {"fetch_params": ["systray_get_activities"]}).get('Store', {}).get('activityGroups', [])

        for model_name, msg, (exp_total, exp_today, exp_planned, exp_overdue) in [
            ('mail.activity', 'Non accessible: deleted', (1, 1, 2, 0)),
            (self.test_record._name, 'Archiving removes activities', (1, 1, 1, 0)),
            (self.test_lead_records._name, 'Accessible (MC with all companies)', (1, 1, 2, 0)),
        ]:
            with self.subTest(model_name=model_name, msg=msg):
                group_values = next(values for values in groups_data if values['model'] == model_name)
                self.assertEqual(group_values['total_count'], exp_total)
                self.assertEqual(group_values['today_count'], exp_today)
                self.assertEqual(group_values['planned_count'], exp_planned)
                self.assertEqual(group_values['overdue_count'], exp_overdue)
                if model_name == 'mail.activity':  # for mail.activity, there is a key with activities we can check
                    self.assertEqual(sorted(group_values['activity_ids']), sorted((self.test_activities_removed + self.test_activities_free).ids))

        # when allowed companies restrict visible records, linked activities are
        # removed from systray, considering you have to log into the right company
        # to see them (change in 18+)
        with freeze_time(self.dt_reference):
            groups_data = self.make_jsonrpc_request("/mail/data", {
                "fetch_params": ["systray_get_activities"],
                "context": {"allowed_company_ids": self.company_admin.ids},
            }).get('Store', {}).get('activityGroups', [])

        for model_name, msg, (exp_total, exp_today, exp_planned, exp_overdue) in [
            ('mail.activity', 'Non accessible: deleted (MC ignored, stripped out like inaccessible records)', (1, 1, 2, 0)),
            (self.test_record._name, 'Archiving removes activities', (1, 1, 1, 0)),
            (self.test_lead_records._name, 'Accessible', (1, 1, 1, 0)),
        ]:
            with self.subTest(model_name=model_name, msg=msg):
                group_values = next(values for values in groups_data if values['model'] == model_name)
                self.assertEqual(group_values['total_count'], exp_total)
                self.assertEqual(group_values['today_count'], exp_today)
                self.assertEqual(group_values['planned_count'], exp_planned)
                self.assertEqual(group_values['overdue_count'], exp_overdue)
                if model_name == 'mail.activity':  # for mail.activity, there is a key with activities we can check
                    self.assertEqual(sorted(group_values['activity_ids']), sorted((self.test_activities_removed + self.test_activities_free).ids))

        # now not having accessible to company 2 records: tread like forbidden
        self.user_employee.write({'company_ids': [(3, self.company_2.id)]})
        with freeze_time(self.dt_reference):
            groups_data = self.make_jsonrpc_request("/mail/data", {
                "fetch_params": ["systray_get_activities"],
                "context": {"allowed_company_ids": self.company_admin.ids},
            }).get('Store', {}).get('activityGroups', [])

        for model_name, msg, (exp_total, exp_today, exp_planned, exp_overdue) in [
            ('mail.activity', 'Non accessible: deleted + company error managed like forbidden record', (1, 1, 3, 0)),
            (self.test_record._name, 'Archiving removes activities', (1, 1, 1, 0)),
            (self.test_lead_records._name, 'Accessible', (1, 1, 1, 0)),
        ]:
            with self.subTest(model_name=model_name, msg=msg):
                group_values = next(values for values in groups_data if values['model'] == model_name)
                self.assertEqual(group_values['total_count'], exp_total)
                self.assertEqual(group_values['today_count'], exp_today)
                self.assertEqual(group_values['planned_count'], exp_planned)
                self.assertEqual(group_values['overdue_count'], exp_overdue)
                if model_name == 'mail.activity':  # for mail.activity, there is a key with activities we can check
                    self.assertEqual(sorted(group_values['activity_ids']), sorted((self.test_activities_removed + self.test_activities_company_2 + self.test_activities_free).ids))