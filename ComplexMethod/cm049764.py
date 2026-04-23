def _execute_message_post_subtests(self, record, tests: list[MessagePostSubTestData]):
        for test in tests:
            self._authenticate_pseudo_user(test.user if (test.user and test.user != self.user_public) else test.guest)
            with self.subTest(record=record, user=test.user.name, guest=test.guest.name, route_kw=test.route_kw):
                if test.allowed:
                    message = self._message_post(record, test.post_data, test.route_kw)
                    if test.guest and not test.exp_author:
                        self.assertEqual(message.author_guest_id, test.guest)
                    else:
                        self.assertEqual(message.author_id, test.exp_author or test.user.partner_id)
                    if test.exp_partners is not None:
                        self.assertEqual(message.partner_ids, test.exp_partners)
                    if test.exp_emails is not None:
                        self.assertEqual(message.partner_ids.mapped("email"), test.exp_emails)
                else:
                    with self.assertRaises(JsonRpcException, msg="werkzeug.exceptions.NotFound"):
                        self._message_post(record, test.post_data, test.route_kw)