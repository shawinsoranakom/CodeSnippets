def assertRecipientsData(self, recipients_data, records, partners, partner_to_users=None):
        """ Custom assert as recipients structure is custom and may change due
        to some implementation choice. """
        if records:
            self.assertEqual(set(recipients_data.keys()), set(records.ids))
            record_ids = records.ids
        else:
            records, record_ids = [False], [0]
        for record, record_id in zip(records, record_ids):
            record_data = recipients_data[record_id]
            self.assertEqual(set(record_data.keys()), set(partners.ids))
            for partner in partners:
                partner_data = record_data[partner.id]
                if partner_to_users and partner_to_users.get(partner.id):  #helps making test explicit
                    user = partner_to_users[partner.id]
                else:
                    user = next((user for user in partner.user_ids if not user.share), self.env['res.users'])
                    if not user:
                        user = next((user for user in partner.user_ids), self.env['res.users'])
                self.assertEqual(partner_data['active'], partner.active)
                self.assertEqual(partner_data['email_normalized'], partner.email_normalized)
                self.assertEqual(partner_data['lang'], partner.lang)
                self.assertEqual(partner_data['name'], partner.name)
                if user:
                    self.assertEqual(partner_data['groups'], set(user.all_group_ids.ids))
                    self.assertEqual(partner_data['notif'], user.notification_type)
                    self.assertEqual(partner_data['uid'], user.id)
                else:
                    self.assertEqual(partner_data['groups'], set())
                    self.assertEqual(partner_data['notif'], 'email')
                    self.assertFalse(partner_data['uid'])
                if record:
                    self.assertEqual(partner_data['is_follower'], partner in record.message_partner_ids)
                else:
                    self.assertFalse(partner_data['is_follower'])
                self.assertEqual(partner_data['share'], partner.partner_share)
                self.assertEqual(partner_data['ushare'], user.share)