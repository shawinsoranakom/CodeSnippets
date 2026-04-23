def _execute_attendee_based(self):
        """ Main scheduler method when running in attendee-based mode aka
        'after_sub'. This relies on a sub model allowing to know which
        registrations have been contacted.

        It currently does two main things
          * generate missing 'event.mail.registrations' which are scheduled
            communication linked to registrations;
          * launch registration-based communication, splitting in batches as
            it may imply a lot of computation. When having more than given
            limit to handle, schedule another call of cron to avoid having to
            wait another cron interval check;
        """
        self.ensure_one()
        context_registrations = self.env.context.get('event_mail_registration_ids')

        auto_commit = not modules.module.current_test
        batch_size = int(
            self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')
        ) or 50  # be sure to not have 0, as otherwise no iteration is done
        cron_limit = int(
            self.env['ir.config_parameter'].sudo().get_param('mail.render.cron.limit')
        ) or 1000  # be sure to not have 0, as otherwise we will loop

        # fillup on subscription lines (generate more than to render creating
        # mail.registration is less costly than rendering emails)
        # note: original 2many domain was
        #   ("id", "not in", self.env["event.registration"]._search([
        #       ("mail_registration_ids.scheduler_id", "in", self.ids),
        #   ]))
        # but it gives less optimized sql
        new_attendee_domain = [
            ('event_id', '=', self.event_id.id),
            ("state", "not in", ("cancel", "draft")),
            ("mail_registration_ids", "not in", self.env["event.mail.registration"]._search(
                [('scheduler_id', 'in', self.ids)]
            )),
        ]
        if context_registrations:
            new_attendee_domain += [
                ('id', 'in', context_registrations),
            ]
        self.env["event.mail.registration"].flush_model(["registration_id", "scheduler_id"])
        new_attendees = self.env["event.registration"].search(new_attendee_domain, limit=cron_limit * 2, order="id ASC")
        new_attendee_mails = self._create_missing_mail_registrations(new_attendees)

        # fetch attendee schedulers to run (or use the one given in context)
        mail_domain = self.env["event.mail.registration"]._get_skip_domain() + [("scheduler_id", "=", self.id)]
        if context_registrations:
            new_attendee_mails = new_attendee_mails.filtered_domain(mail_domain)
        else:
            new_attendee_mails = self.env["event.mail.registration"].search(
                mail_domain,
                limit=(cron_limit + 1), order="id ASC"
            )

        # there are more than planned for the cron -> reschedule
        if len(new_attendee_mails) > cron_limit:
            new_attendee_mails = new_attendee_mails[:cron_limit]
            self.env.ref('event.event_mail_scheduler')._trigger()

        for chunk in tools.split_every(batch_size, new_attendee_mails.ids, self.env["event.mail.registration"].browse):
            # filter out canceled / draft, and compare to seats_taken (same heuristic)
            valid_chunk = chunk.filtered(lambda m: m.registration_id.state not in ("draft", "cancel"))
            # scheduled mails for draft / cancel should be removed as they won't be sent
            (chunk - valid_chunk).unlink()

            # send communications, then update only when being in cron mode (aka no
            # context registrations) to avoid concurrent updates on scheduler
            valid_chunk._execute_on_registrations()
            # if not context_registrations:
            self._refresh_mail_count_done()
            if auto_commit:
                self.env.cr.commit()
                # invalidate cache, no need to keep previous content in memory
                self.env.invalidate_all()