def test_access_create(self):
        """ Test 'group_user' creation rules """
        # prepare 'notified of parent' condition
        admin_msg = self.record_admin.message_ids[-1]
        admin_msg.write({'partner_ids': [(4, self.user_employee.partner_id.id)]})

        # prepare 'followers' condition
        record_admin_fol = self.env['mail.test.access'].create({
            'access': 'admin',
            'name': 'Admin Record Follower',
        })
        record_admin_fol.message_subscribe(self.user_employee.partner_id.ids)

        for record, msg_vals, should_crash, reason in [
            # private-like
            (self.env["mail.test.access"], {}, False, 'Private message like is ok'),
            # document based
            (self.record_internal, {}, False, 'W Access on record'),
            (self.record_internal, {'message_type': 'notification'}, False, 'W Access on record, notification does not change anything'),
            (self.record_internal_ro, {}, True, 'No W Access on record'),
            (self.record_admin, {}, True, 'No access on record (and not notified on first message)'),
            (record_admin_fol, {
                'reply_to': 'avoid.catchall@my.test.com',  # otherwise crashes
            }, False, 'Followers > no access on record'),
            # parent based
            (self.record_admin, {  # note: force reply_to normally computed by message_post avoiding ACLs issues
                'parent_id': admin_msg.id,
            }, False, 'No access on record but reply to notified parent'),
        ]:
            with self.subTest(record=record, msg_vals=msg_vals, reason=reason):
                final_vals = dict(
                    {
                        'body': 'Test',
                        'message_type': 'comment',
                        'subtype_id': self.env.ref('mail.mt_comment').id,
                    }, **msg_vals
                )
                if should_crash:
                    with self.assertRaises(AccessError):
                        self.env['mail.message'].with_user(self.user_employee).create({
                            'model': record._name if record else False,
                            'res_id': record.id if record else False,
                            **final_vals,
                        })
                    if record:
                        with self.assertRaises(AccessError):
                            record.with_user(self.user_employee).message_post(
                                **final_vals,
                            )
                else:
                    _message = self.env['mail.message'].with_user(self.user_employee).create({
                        'model': record._name if record else False,
                        'res_id': record.id if record else False,
                        **final_vals,
                    })
                    if record:
                        # TDE note: due to parent_id flattening, doing message_post
                        # with parent_id which should allow posting crashes, as
                        # parent_id is changed to an older message the employee cannot
                        # access. Won't fix that in stable.
                        if record == self.record_admin and 'parent_id' in msg_vals:
                            continue
                        record.with_user(self.user_employee).message_post(
                            **final_vals,
                        )