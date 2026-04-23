def test_assert_initial_values(self):
        """ Just ensure tests data """
        for record in (
            self.record_public + self.record_portal + self.record_portal_ro + self.record_followers +
            self.record_internal + self.record_internal_ro + self.record_admin):
            self.assertFalse(record.message_follower_ids)
            self.assertEqual(len(record.message_ids), 3)

            for index, msg in enumerate(record.message_ids):
                body = ['<p>Test Answer</p>', '<p>Test Comment</p>', '<p>Mail Access Test created</p>'][index]
                message_type = ['comment', 'comment', 'notification'][index]
                subtype_id = [self.env.ref('mail.mt_comment'), self.env.ref('mail.mt_comment'), self.env.ref('mail.mt_note')][index]
                self.assertEqual(msg.author_id, self.partner_root)
                self.assertEqual(msg.body, body)
                self.assertEqual(msg.message_type, message_type)
                self.assertFalse(msg.notified_partner_ids)
                self.assertFalse(msg.partner_ids)
                self.assertEqual(msg.subtype_id, subtype_id)

        # public user access check
        for allowed in self.record_public:
            allowed.with_user(self.user_public).read(['name'])
        for forbidden in self.record_portal + self.record_portal_ro + self.record_followers + self.record_internal + self.record_internal_ro + self.record_admin:
            with self.assertRaises(AccessError):
                forbidden.with_user(self.user_public).read(['name'])
        for forbidden in self.record_public + self.record_portal + self.record_portal_ro + self.record_followers + self.record_internal + self.record_internal_ro + self.record_admin:
            with self.assertRaises(AccessError):
                forbidden.with_user(self.user_public).write({'name': 'Update'})

        # portal user access check
        for allowed in self.record_public + self.record_portal + self.record_portal_ro:
            allowed.with_user(self.user_portal).read(['name'])
        for forbidden in self.record_internal + self.record_internal_ro + self.record_admin:
            with self.assertRaises(AccessError):
                forbidden.with_user(self.user_portal).read(['name'])
        for allowed in self.record_portal:
            allowed.with_user(self.user_portal).write({'name': 'Update'})
        for forbidden in self.record_public + self.record_portal_ro + self.record_followers + self.record_internal + self.record_internal_ro + self.record_admin:
            with self.assertRaises(AccessError):
                forbidden.with_user(self.user_portal).write({'name': 'Update'})
        self.record_followers.message_subscribe(self.user_portal.partner_id.ids)
        self.record_followers.with_user(self.user_portal).read(['name'])
        self.record_followers.with_user(self.user_portal).write({'name': 'Update'})

        # internal user access check
        for allowed in self.record_public + self.record_portal + self.record_portal_ro + self.record_followers + self.record_internal + self.record_internal_ro:
            allowed.with_user(self.user_employee).read(['name'])
        for forbidden in self.record_admin:
            with self.assertRaises(AccessError):
                forbidden.with_user(self.user_employee).read(['name'])
        for allowed in self.record_public + self.record_portal + self.record_portal_ro + self.record_followers + self.record_internal:
            allowed.with_user(self.user_employee).write({'name': 'Update'})
        for forbidden in self.record_internal_ro + self.record_admin:
            with self.assertRaises(AccessError):
                forbidden.with_user(self.user_employee).write({'name': 'Update'})

        # elevated user access check
        for allowed in self.record_public + self.record_portal + self.record_portal_ro + self.record_followers + self.record_internal + self.record_internal_ro + self.record_admin:
            allowed.with_user(self.user_admin).read(['name'])