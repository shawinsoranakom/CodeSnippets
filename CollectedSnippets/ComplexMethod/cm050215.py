def test_notify_recipients_internals(self):
        base_record = self.test_record.with_env(self.env)
        pdata = self._generate_notify_recipients(self.partner_1 | self.partner_employee)
        msg_vals = {
            'body': 'Message body',
            'model': base_record._name,
            'res_id': base_record.id,
            'subject': 'Message subject',
        }
        link_vals = {
            'token': 'token_val',
            'access_token': 'access_token_val',
            'auth_signup_token': 'auth_signup_token_val',
            'auth_login': 'auth_login_val',
        }
        notify_msg_vals = dict(msg_vals, **link_vals)

        # test notifying the class (void recordset)
        classify_res = self.env[base_record._name]._notify_get_recipients_classify(
            self.env['mail.message'], pdata, 'My Custom Model Name',
            msg_vals=notify_msg_vals,
        )
        # find back information for each recipients
        partner_info = next(item for item in classify_res if item['recipients_ids'] == self.partner_1.ids)
        emp_info = next(item for item in classify_res if item['recipients_ids'] == self.partner_employee.ids)
        # partner: no access button
        self.assertFalse(partner_info['has_button_access'])
        # employee: access button and link
        self.assertTrue(emp_info['has_button_access'])
        for param, value in link_vals.items():
            self.assertIn(f'{param}={value}', emp_info['button_access']['url'])
        self.assertIn(f'model={base_record._name}', emp_info['button_access']['url'])
        self.assertIn(f'res_id={base_record.id}', emp_info['button_access']['url'])
        self.assertNotIn('body', emp_info['button_access']['url'])
        self.assertNotIn('subject', emp_info['button_access']['url'])

        # test when notifying on non-records (e.g. MailThread._message_notify())
        for model, res_id in ((base_record._name, False),
                              (base_record._name, 0),  # browse(0) does not return a valid recordset
                              ('mail.thread', False),
                              ('mail.thread', base_record.id)):
            with self.subTest(model=model, res_id=res_id):
                notify_msg_vals.update({
                    'model': model,
                    'res_id': res_id,
                })
                classify_res = self.env[model].browse(res_id)._notify_get_recipients_classify(
                    self.env['mail.message'], pdata, 'Test',
                    msg_vals=notify_msg_vals,
                )
                # find back information for partner
                partner_info = next(item for item in classify_res if item['recipients_ids'] == self.partner_1.ids)
                emp_info = next(item for item in classify_res if item['recipients_ids'] == self.partner_employee.ids)
                # check there is no access button
                self.assertFalse(partner_info['has_button_access'])
                self.assertFalse(emp_info['has_button_access'])

        # test when notifying based a valid record, but asking for a falsy record in msg_vals
        for model, res_id in ((base_record._name, False),
                              (base_record._name, 0),  # browse(0) does not return a valid recordset
                              (False, base_record.id),
                              (False, False),
                              ('mail.thread', False),
                              ('mail.thread', base_record.id)):
            with self.subTest(model=model, res_id=res_id):
                # note that msg_vals wins over record on which method is called
                notify_msg_vals.update({
                    'model': model,
                    'res_id': res_id,
                })
                classify_res = base_record._notify_get_recipients_classify(
                    self.env['mail.message'], pdata, 'Test',
                    msg_vals=notify_msg_vals,
                )
                # find back information for partner
                partner_info = next(item for item in classify_res if item['recipients_ids'] == self.partner_1.ids)
                emp_info = next(item for item in classify_res if item['recipients_ids'] == self.partner_employee.ids)
                # check there is no access button
                self.assertFalse(partner_info['has_button_access'])
                self.assertFalse(emp_info['has_button_access'])