def test_notify_update_activities(self):
        write_vals_all = [
            # added to counter for employee 2, removed from counter for current employee
            {'user_id': self.user_employee_2.id},
            {'user_id': self.user_employee_2.id, 'date_deadline': datetime(2023, 12, 31, 15, 0, 0), 'active': True},
            # just notify
            {'date_deadline': datetime(2024, 1, 2, 15, 0, 0)},  # everything is in the future -> all removed from counter
            {'date_deadline': datetime(2023, 12, 31, 15, 0, 0)},  # everything is in the past -> the one from the future is added
            {'active': False},  # everything is archived -> all removed from counter
            {'active': True},  # the archived one is unarchived -> added to counter
            {},  # no "to be done" count change -> no notif
            [{'date_deadline': datetime(2024, 1, 2, 15, 0, 0), 'active': True}, {}, {}, {}],
        ]

        expected_notifs = [
            # transfer 4 activities to the second employee, 2 todos taken and 2 given
            [
                ([(self.env.cr.dbname, user.partner_id._name, user.partner_id.id)], [{
                    "type": "mail.activity/updated",
                    "payload": {
                        "count_diff": count_diff,
                    } | ({"activity_created": True} if count_diff > 0 else {"activity_deleted": True}),
                }])
                for user, count_diff
                in zip(self.user_employee + self.user_employee_2, [-2, 2])
            ],
            # transfer 4 activities to the second employee, 2 todos are taken and 4 are given
            [
                ([(self.env.cr.dbname, user.partner_id._name, user.partner_id.id)], [{
                    "type": "mail.activity/updated",
                    "payload": {
                        "count_diff": count_diff,
                    } | ({"activity_created": True} if count_diff > 0 else {"activity_deleted": True}),
                }])
                for user, count_diff
                in zip(self.user_employee + self.user_employee_2, [-2, 4])
            ],
        ] + [[
                ([(self.env.cr.dbname, self.user_employee.partner_id._name, self.user_employee.partner_id.id)], [{
                    "type": "mail.activity/updated",
                    "payload": {
                        "count_diff": count_diff,
                    } | ({"activity_created": True} if count_diff > 0 else {"activity_deleted": True}),
                }])
            ] for count_diff in (-2, 1, -2, 1)
        ] + [
            [([], [])],  # no change -> no notif
            [([], [])],  # no change in "todo" count -> no notif
        ]
        for write_vals, expected_notif_vals in zip(write_vals_all, expected_notifs):
            with self.subTest(vals=write_vals):
                _past_archived, _past_active, _today, _tomorrow = activities = self.env['mail.activity'].create(self.activity_vals)
                self._reset_bus()
                if isinstance(write_vals, list):
                    for activity, vals in zip(activities, write_vals):
                        activity.write(vals)
                else:
                    activities.write(write_vals)
                for (notif_channels, notif_messages) in expected_notif_vals:
                    self.assertBusNotifications(notif_channels, notif_messages)
                activities.unlink()