def test_event_creation_for_user(self):
        """Check that either emails or synchronization happens correctly when creating an event for another user."""
        user_root = self.env.ref('base.user_root')
        self.assertFalse(user_root.microsoft_calendar_token)
        partner = self.env['res.partner'].create({'name': 'Jean-Luc', 'email': 'jean-luc@opoo.com'})
        event_values = {
            'name': 'Event',
            'need_sync_m': True,
            'start': datetime(2020, 1, 15, 8, 0),
            'stop': datetime(2020, 1, 15, 18, 0),
        }
        paused_sync_user = self.users[2]
        paused_sync_user.write({
            'email': 'ms.sync.paused@test.lan',
            'microsoft_synchronization_stopped': True,
            'name': 'Paused Microsoft Sync User',
            'login': 'ms_sync_paused_user',
        })
        self.assertTrue(paused_sync_user.microsoft_synchronization_stopped)
        for create_user, organizer, mail_notified_partners, attendee in [
            (user_root, self.users[0], partner + self.users[0].partner_id, partner),  # emulates online appointment with user 0
            (user_root, None, partner, partner),  # emulates online resource appointment
            (self.users[0], None, False, partner),
            (self.users[0], self.users[0], False, partner),
            (self.users[0], self.users[1], False, partner),
            # create user has paused sync and organizer can sync -> will not sync because of bug
            # only the organizer is notified as we don't notify the author (= create_user.partner_id) on creation
            (paused_sync_user, self.users[0], self.users[0].partner_id, paused_sync_user.partner_id),
        ]:
            with self.subTest(create_uid=create_user.name if create_user else None, user_id=organizer.name if organizer else None, attendee=attendee.name):
                with self.mock_mail_gateway(), patch.object(MicrosoftCalendarService, 'insert') as mock_insert:
                    mock_insert.return_value = ('1', '1')
                    self.env['calendar.event'].with_user(create_user).create({
                        **event_values,
                        'partner_ids': [(4, organizer.partner_id.id), (4, attendee.id)] if organizer else [(4, attendee.id)],
                        'user_id': organizer.id if organizer else False,
                    })
                    self.env.cr.postcommit.run()
                if not mail_notified_partners:
                    self.assertNotSentEmail()
                    mock_insert.assert_called_once()
                    self.assert_dict_equal(mock_insert.call_args[0][0]['organizer'], {
                        'emailAddress': {'address': organizer.email if organizer else '', 'name': organizer.name if organizer else ''}
                    })
                else:
                    mock_insert.assert_not_called()
                    for notified_partner in mail_notified_partners:
                        self.assertMailMail(notified_partner, 'sent', author=(organizer or create_user).partner_id)