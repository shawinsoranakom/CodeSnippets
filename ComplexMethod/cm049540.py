def test_event_mail_schedule(self):
        """ Test mail scheduling for events """
        test_event = self.test_event.with_env(self.env)
        now = self.reference_now
        schedulers = self.env['event.mail'].search([('event_id', '=', test_event.id)])
        after_sub_scheduler = schedulers.filtered(lambda s: s.interval_type == 'after_sub' and s.interval_unit == 'now')
        after_sub_scheduler_2 = schedulers.filtered(lambda s: s.interval_type == 'after_sub' and s.interval_unit == 'hours')
        event_prev_scheduler = schedulers.filtered(lambda s: s.interval_type == 'before_event')
        event_next_scheduler = schedulers.filtered(lambda s: s.interval_type == 'after_event')

        # check iterative work, update params to check call count
        batch_size, render_limit = 2, 10
        self.env['ir.config_parameter'].sudo().set_param('mail.batch_size', batch_size)
        self.env['ir.config_parameter'].sudo().set_param('mail.render.cron.limit', render_limit)

        # create some registrations
        EventMailRegistration = type(self.env['event.mail.registration'])
        exec_origin = EventMailRegistration._execute_on_registrations
        with patch.object(
                EventMailRegistration, '_execute_on_registrations', autospec=True, wraps=EventMailRegistration, side_effect=exec_origin,
             ) as mock_exec, \
             self.mock_datetime_and_now(now), self.mock_mail_gateway(), \
             self.capture_triggers('event.event_mail_scheduler') as capture:
            attendees = self.env['event.registration'].with_user(self.user_eventuser).create([
                {
                    'event_id': test_event.id,
                    'name': f'Reg{idx}',
                    'email': f'reg1{idx}@example.com',
                } for idx in range(15)] + [{
                    'event_id': test_event.id,
                    'name': 'RegDraft',
                    'email': 'reg_draft@example.com',
                    'state': 'draft',
                }, {
                    'event_id': test_event.id,
                    'name': 'RegCancel',
                    'email': 'reg_cancel@example.com',
                    'state': 'cancel',
                }
            ])

        # iterative check
        self.assertEqual(
            mock_exec.call_count, 5,
            "Should have called 5 times execution (batch of 2 until 10 registrations)"
        )

        # REGISTRATIONS / PRE SCHEDULERS
        # --------------------------------------------------

        # check registration state
        self.assertTrue(all(reg.state == 'open' for reg in attendees[:15]), 'Registrations: should be auto-confirmed')
        self.assertListEqual(attendees[15:].mapped('state'), ['draft', 'cancel'])
        self.assertTrue(all(reg.create_date == now for reg in attendees), 'Registrations: should have open date set to confirm date')

        # verify that subscription scheduler was auto-executed after each registration
        self.assertEqual(
            len(after_sub_scheduler.mail_registration_ids), 15,
            'Should have 15 scheduled communication (1 / registration), as we schedule more'
            'than cron limit as create should be quick.')
        for idx, mail_registration in enumerate(after_sub_scheduler.mail_registration_ids):
            self.assertEqual(mail_registration.scheduled_date, now.replace(microsecond=0))
            if idx < 10:
                self.assertTrue(mail_registration.mail_sent, 'event: registration mail should be sent at registration creation')
            else:
                self.assertFalse(mail_registration.mail_sent, 'event: registration mail should be scheduled, too much for limit')
        self.assertEqual(after_sub_scheduler.mail_state, 'running')
        self.assertEqual(after_sub_scheduler.mail_count_done, 10, 'event: not all subscription mails should have been sent as too much for limit')

        # cron should have been triggered for the remaining registrations
        self.assertSchedulerCronTriggers(capture, [now])

        # check emails effectively sent
        self.assertEqual(len(self._new_mails), 10, 'event: should have 10 scheduled emails (1 / executed registration)')
        self.assertMailMailWEmails(
            [formataddr((reg.name, reg.email)) for reg in attendees[:10]],
            'outgoing',
            content=None,
            fields_values={
                'email_from': self.user_eventmanager.company_id.email_formatted,
                'subject': f'Confirmation for {test_event.name}',
            })

        # same for second scheduler: scheduled but not sent
        self.assertEqual(
            len(after_sub_scheduler_2.mail_registration_ids), 15,
            'Should have 15 scheduled communication (1 / registration)')
        for mail_registration in after_sub_scheduler_2.mail_registration_ids:
            self.assertEqual(mail_registration.scheduled_date, now.replace(microsecond=0) + relativedelta(hours=1))
            self.assertFalse(mail_registration.mail_sent, 'event: registration mail should be scheduled, not sent')
        self.assertEqual(after_sub_scheduler_2.mail_count_done, 0, 'event: all subscription mails should be scheduled, not sent')

        # RE-RUN SCHEDULER TO COMPLETE SENDING
        # --------------------------------------------------

        with patch.object(
               EventMailRegistration, '_execute_on_registrations', autospec=True, wraps=EventMailRegistration, side_effect=exec_origin,
            ) as mock_exec:
            capture = self.execute_event_cron(freeze_date=now)

        # iterative check
        self.assertEqual(
            mock_exec.call_count, 3,
            "Should have called 3 times execution (batch of 2 with 5 registrations left = 3 iterations)"
        )

        # verify that subscription scheduler was auto-executed after each registration
        self.assertEqual(len(after_sub_scheduler.mail_registration_ids), 15)
        for mail_registration in after_sub_scheduler.mail_registration_ids:
            self.assertEqual(mail_registration.scheduled_date, now.replace(microsecond=0))
            self.assertTrue(mail_registration.mail_sent)
        self.assertEqual(after_sub_scheduler.mail_state, 'running')
        self.assertEqual(
            after_sub_scheduler.mail_count_done, 15,
            'Should have sent all mails, as cron limit is set to 20'
        )

        # check emails effectively sent
        self.assertEqual(len(self._new_mails), 5, 'event: should have 5 scheduled emails (1 / executed registration)')
        self.assertMailMailWEmails(
            [formataddr((reg.name, reg.email)) for reg in attendees[10:15]],
            'outgoing',
            content=None,
            fields_values={
                'email_from': self.user_eventmanager.company_id.email_formatted,
                'subject': f'Confirmation for {test_event.name}',
            })

        # SECOND ATTENDEE-BASED SCHEDULER (LATER) - UPDATE ITERATIVE
        # --------------------------------------------------

        # check default behavior, batch of 50 to run up to 1000 attendees
        self.env['ir.config_parameter'].sudo().set_param('mail.batch_size', False)
        self.env['ir.config_parameter'].sudo().set_param('mail.render.cron.limit', False)

        # execute event reminder scheduler explicitly, before scheduled date -> should not do anything
        with self.mock_datetime_and_now(now), self.mock_mail_gateway():
            after_sub_scheduler_2.execute()
        self.assertFalse(any(mail_reg.mail_sent for mail_reg in after_sub_scheduler_2.mail_registration_ids))
        self.assertEqual(after_sub_scheduler_2.mail_count_done, 0)
        self.assertEqual(len(self._new_mails), 0, 'event: should not send mails before scheduled date')

        # execute event reminder scheduler, right at scheduled date -> should sent mails
        now_registration = now + relativedelta(hours=1)
        with patch.object(
                EventMailRegistration, '_execute_on_registrations', autospec=True, wraps=EventMailRegistration, side_effect=exec_origin,
             ) as mock_exec:
            capture = self.execute_event_cron(freeze_date=now_registration)

        # iterative check
        self.assertEqual(
            mock_exec.call_count, 1,
            "Should have called 1 times execution (batch of 50 with 15 registrations = 1 iteration)"
        )

        # verify that subscription scheduler was auto-executed after each registration
        self.assertEqual(len(after_sub_scheduler_2.mail_registration_ids), 15, 'event: should have 15 scheduled communication (1 / registration)')
        self.assertTrue(all(mail_reg.mail_sent for mail_reg in after_sub_scheduler_2.mail_registration_ids))
        self.assertEqual(after_sub_scheduler_2.mail_state, 'running')
        self.assertEqual(after_sub_scheduler_2.mail_count_done, 15,
                         'All subscriptions emails should have been sent')

        # check emails effectively sent
        self.assertEqual(len(self._new_mails), 15, 'event: should have 15 scheduled emails (1 / registration)')
        self.assertMailMailWEmails(
            [formataddr((reg.name, reg.email)) for reg in attendees[:15]],
            'outgoing',
            content=None,
            fields_values={
                'email_from': self.user_eventmanager.company_id.email_formatted,
                'subject': f'Confirmation for {test_event.name}',
            })

        # PRE SCHEDULERS (MOVE FORWARD IN TIME)
        # --------------------------------------------------

        self.assertFalse(event_prev_scheduler.mail_done)
        self.assertEqual(event_prev_scheduler.mail_state, 'scheduled')

        # simulate cron running before scheduled date -> should not do anything
        now_start = self.event_date_begin + relativedelta(hours=-25, microsecond=654321)
        self.execute_event_cron(freeze_date=now_start)

        self.assertFalse(event_prev_scheduler.mail_done)
        self.assertEqual(event_prev_scheduler.mail_state, 'scheduled')
        self.assertEqual(event_prev_scheduler.mail_count_done, 0)
        self.assertEqual(len(self._new_mails), 0)

        # execute cron to run schedulers after scheduled date
        now_start = self.event_date_begin + relativedelta(hours=-23, microsecond=654321)
        self.execute_event_cron(freeze_date=now_start)

        # check that scheduler is finished
        self.assertTrue(event_prev_scheduler.mail_done, 'event: reminder scheduler should have run')
        self.assertEqual(event_prev_scheduler.mail_state, 'sent', 'event: reminder scheduler should have run')

        # check emails effectively sent
        self.assertEqual(len(self._new_mails), 15, 'event: should have scheduled 15 mails (1 / registration)')
        self.assertMailMailWEmails(
            [formataddr((reg.name, reg.email)) for reg in attendees[:15]],
            'outgoing',
            content=None,
            fields_values={
                'email_from': self.user_eventmanager.company_id.email_formatted,
                'subject': f'Reminder for {test_event.name}: tomorrow',
            })

        # NEW REGISTRATION EFFECT ON SCHEDULERS
        # --------------------------------------------------

        with self.mock_datetime_and_now(now_start), self.mock_mail_gateway():
            new_attendee = self.env['event.registration'].create({
                'event_id': test_event.id,
                'name': 'Reg3',
                'email': 'reg3@example.com',
                'state': 'draft',
            })

        # no more seats
        self.assertEqual(new_attendee.state, 'draft')

        # schedulers state untouched
        self.assertTrue(event_prev_scheduler.mail_done)
        self.assertFalse(event_next_scheduler.mail_done)

        # confirm registration -> should trigger registration schedulers
        # NOTE: currently all schedulers are based on create_date
        # meaning several communications may be sent in the time time
        with self.mock_datetime_and_now(now_start + relativedelta(hours=1)), self.mock_mail_gateway():
            new_attendee.action_confirm()

        # verify that subscription scheduler was auto-executed after new registration confirmed
        self.assertEqual(len(after_sub_scheduler.mail_registration_ids), 16, 'event: should have 16 scheduled communication (1 / registration)')
        new_mail_reg = after_sub_scheduler.mail_registration_ids.filtered(lambda mail_reg: mail_reg.registration_id == new_attendee)
        self.assertEqual(new_mail_reg.scheduled_date, now_start.replace(microsecond=0))
        self.assertTrue(new_mail_reg.mail_sent, 'event: registration mail should be sent at registration creation')
        self.assertEqual(after_sub_scheduler.mail_count_done, 16,
                         'event: all subscription mails should have been sent')
        # verify that subscription scheduler was auto-executed after new registration confirmed
        self.assertEqual(len(after_sub_scheduler_2.mail_registration_ids), 16, 'event: should have 16 scheduled communication (1 / registration)')
        new_mail_reg = after_sub_scheduler_2.mail_registration_ids.filtered(lambda mail_reg: mail_reg.registration_id == new_attendee)
        self.assertEqual(new_mail_reg.scheduled_date, now_start.replace(microsecond=0) + relativedelta(hours=1))
        self.assertTrue(new_mail_reg.mail_sent, 'event: registration mail should be sent at registration creation')
        self.assertEqual(after_sub_scheduler_2.mail_count_done, 16,
                         'event: all subscription mails should have been sent')

        # check emails effectively sent
        self.assertEqual(len(self._new_mails), 2, 'event: should have 1 scheduled emails (new registration only)')
        # manual check because 2 identical mails are sent and mail tools do not support it easily
        for mail in self._new_mails:
            self.assertEqual(mail.email_from, self.user_eventmanager.company_id.email_formatted)
            self.assertEqual(mail.subject, f'Confirmation for {test_event.name}')
            self.assertEqual(mail.state, 'outgoing')
            self.assertEqual(mail.email_to, formataddr((new_attendee.name, new_attendee.email)))

        # POST SCHEDULERS (MOVE FORWARD IN TIME)
        # --------------------------------------------------

        self.assertFalse(event_next_scheduler.mail_done)

        # execute event reminder scheduler explicitly after its schedule date
        new_end = self.event_date_end + relativedelta(hours=2)
        (attendees + new_attendee).invalidate_recordset(['event_date_range'])
        self.execute_event_cron(freeze_date=new_end)

        # check that scheduler is finished
        self.assertTrue(event_next_scheduler.mail_done, 'event: reminder scheduler should should have run')
        self.assertEqual(event_next_scheduler.mail_state, 'sent', 'event: reminder scheduler should have run')
        self.assertEqual(event_next_scheduler.mail_count_done, 16)

        # check emails effectively sent
        self.assertEqual(len(self._new_mails), 16, 'event: should have scheduled 3 mails, one for each registration')
        self.assertMailMailWEmails(
        [formataddr((reg.name, reg.email)) for reg in attendees[:15] + new_attendee],
            'outgoing',
            content=None,
            fields_values={
                'email_from': self.user_eventmanager.company_id.email_formatted,
                'subject': f"Reminder for {test_event.name}: today",
            })