def test_recipients_fetch(self):
        test_records = self.env['mail.test.simple'].create([
            {'email_from': 'ignasse@example.com',
             'name': 'Test %s' % idx,
            } for idx in range(5)
        ])
        # make followers listen to notes to use it and check portal will never be notified of it (internal)
        test_records.message_follower_ids.sudo().write({'subtype_ids': [(4, self.env.ref('mail.mt_note').id)]})
        for test_record in test_records:
            self.assertEqual(test_record.message_partner_ids, self.env.user.partner_id)

        test_records[0].message_subscribe(self.partner_portal.ids)
        self.assertNotIn(
            self.env.ref('mail.mt_note'),
            test_records[0].message_follower_ids.filtered(lambda fol: fol.partner_id == self.partner_portal).subtype_ids,
            'Portal user should not follow notes by default')

        # just fetch followers
        recipients_data = self.env['mail.followers']._get_recipient_data(
            test_records[0], 'comment', self.env.ref('mail.mt_comment').id,
            pids=None
        )
        self.assertRecipientsData(recipients_data, test_records[0], self.env.user.partner_id + self.partner_portal)

        # followers + additional recipients
        recipients_data = self.env['mail.followers']._get_recipient_data(
            test_records[0], 'comment', self.env.ref('mail.mt_comment').id,
            pids=(self.customer + self.common_partner + self.partner_admin).ids
        )
        self.assertRecipientsData(recipients_data, test_records[0],
                                  self.env.user.partner_id + self.partner_portal + self.customer + self.common_partner + self.partner_admin)

        # ensure filtering on internal: should exclude Portal even if misconfiguration
        follower_portal = test_records[0].message_follower_ids.filtered(lambda fol: fol.partner_id == self.partner_portal).sudo()
        follower_portal.write({'subtype_ids': [(4, self.env.ref('mail.mt_note').id)]})
        follower_portal.flush_recordset()
        recipients_data = self.env['mail.followers']._get_recipient_data(
            test_records[0], 'comment', self.env.ref('mail.mt_note').id,
            pids=(self.common_partner + self.partner_admin).ids
        )
        self.assertRecipientsData(recipients_data, test_records[0], self.env.user.partner_id + self.common_partner + self.partner_admin)

        # ensure filtering on subtype: should exclude Portal as it does not follow comment anymore
        follower_portal.write({'subtype_ids': [(3, self.env.ref('mail.mt_comment').id)]})
        recipients_data = self.env['mail.followers']._get_recipient_data(
            test_records[0], 'comment', self.env.ref('mail.mt_comment').id,
            pids=(self.common_partner + self.partner_admin).ids
        )
        self.assertRecipientsData(recipients_data, test_records[0], self.env.user.partner_id + self.common_partner + self.partner_admin)

        # check without subtype
        recipients_data = self.env['mail.followers']._get_recipient_data(
            test_records[0], 'comment', False,
            pids=(self.common_partner + self.partner_admin).ids
        )
        self.assertRecipientsData(recipients_data, test_records[0], self.common_partner + self.partner_admin)

        # multi mode
        test_records[1].message_subscribe(self.partner_portal.ids)
        test_records[0:4].message_subscribe(self.common_partner.ids)
        recipients_data = self.env['mail.followers']._get_recipient_data(
            test_records, 'comment', self.env.ref('mail.mt_comment').id,
            pids=self.partner_admin.ids
        )
        # 0: portal is follower but does not follow comment + common partner (+ admin as pid)
        recipients_data_1 = dict((r, recipients_data[r]) for r in recipients_data if r in  test_records[0:1].ids)
        self.assertRecipientsData(recipients_data_1, test_records[0:1], self.env.user.partner_id + self.common_partner + self.partner_admin)
        # 1: portal is follower with comment + common partner (+ admin as pid)
        recipients_data_1 = dict((r, recipients_data[r]) for r in recipients_data if r in  test_records[1:2].ids)
        self.assertRecipientsData(recipients_data_1, test_records[1:2], self.env.user.partner_id + self.common_partner + self.partner_portal + self.partner_admin)
        # 2-3: common partner (+ admin as pid)
        recipients_data_2 = dict((r, recipients_data[r]) for r in recipients_data if r in  test_records[2:4].ids)
        self.assertRecipientsData(recipients_data_2, test_records[2:4], self.env.user.partner_id + self.common_partner + self.partner_admin)
        # 4+: env user partner (+ admin as pid)
        recipients_data_3 = dict((r, recipients_data[r]) for r in recipients_data if r in  test_records[4:].ids)
        self.assertRecipientsData(recipients_data_3, test_records[4:], self.env.user.partner_id + self.partner_admin)

        # multi mode, pids only
        recipients_data = self.env['mail.followers']._get_recipient_data(
            test_records, 'comment', False,
            pids=(self.env.user.partner_id + self.partner_admin).ids
        )
        self.assertRecipientsData(recipients_data, test_records, self.env.user.partner_id + self.partner_admin)

        # on mail.thread, False everywhere: pathologic case
        test_partners = self.partner_admin + self.partner_employee + self.common_partner
        recipients_data = self.env['mail.followers']._get_recipient_data(
            self.env['mail.thread'], False, False,
            pids=test_partners.ids
        )
        self.assertRecipientsData(recipients_data, False, test_partners)