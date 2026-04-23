def test_leave_ooo(self):
        self.assertNotEqual(self.employee_hruser.user_id.im_status, 'leave_offline', 'user should not be on leave')
        self.assertNotEqual(self.employee_hruser.user_id.partner_id.im_status, 'leave_offline', 'user should not be on leave')
        # validate a leave from 2024-06-05 (Wednesday) to 2024-06-07 (Friday)
        first_leave = self.env['hr.leave'].create({
            'name': 'Christmas',
            'employee_id': self.employee_hruser.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': "2024-06-05",
            'request_date_to': "2024-06-07",
        })
        first_leave.action_approve()
        # validate a leave from 2024-06-10 (Monday) to 2024-06-11 (Tuesday)
        second_leave = self.env['hr.leave'].create({
            'name': 'Christmas',
            'employee_id': self.employee_hruser.id,
            'holiday_status_id': self.leave_type.id,
            'request_date_from': "2024-06-10",
            'request_date_to': "2024-06-11",
        })
        second_leave.action_approve()
        # missing dependencies on compute functions
        self.employee_hruser.user_id.invalidate_recordset(["im_status"])
        self.employee_hruser.user_id.partner_id.invalidate_recordset(["im_status"])
        self.assertEqual(self.employee_hruser.user_id.im_status, 'leave_offline', 'user should be out (leave_offline)')
        self.assertEqual(self.employee_hruser.user_id.partner_id.im_status, 'leave_offline', 'user should be out (leave_offline)')

        partner = self.employee_hruser.user_id.partner_id
        partner2 = self.user_employee.partner_id

        channel = self.env['discuss.channel'].with_user(self.user_employee).with_context({
            'mail_create_nolog': True,
            'mail_create_nosubscribe': True,
        }).create({
            'channel_partner_ids': [(4, partner.id), (4, partner2.id)],
            'channel_type': 'chat',
            'name': 'test'
        })
        data = Store().add(channel).get_result()
        partner_info = next(p for p in data["res.partner"] if p["id"] == partner.id)
        partner2_info = next(p for p in data["res.partner"] if p["id"] == partner2.id)
        user_info = next(u for u in data["res.users"] if u["id"] == partner_info["main_user_id"])
        user2_info = next(u for u in data["res.users"] if u["id"] == partner2_info["main_user_id"])
        employee_info = next(e for e in data["hr.employee"] if e["id"] == user_info["employee_ids"][0])
        employee2_info = next(e for e in data["hr.employee"] if e["id"] == user2_info["employee_ids"][0])
        self.assertFalse(employee2_info["leave_date_to"], "current user should not be out of office")
        # The employee will be back in the office the day after his second leave ends
        self.assertEqual(
            employee_info["leave_date_to"], "2024-06-12", "correspondent should be out of office"
        )
        self.assertEqual(
            self.employee_hruser.user_id.with_context(formatted_display_name=True).display_name,
            'armande (base.group_user,hr_holidays.group_hr_holidays_user) \t ✈ --Back on Jun 12, 2024--',
            'formatted display name should show the "Back on" formatted date'
        )