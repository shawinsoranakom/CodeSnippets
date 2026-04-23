def _execute_event_based(self, mail_slot=False):
        """ Main scheduler method when running in event-based mode aka
        'after_event' or 'before_event' (and their negative counterparts).
        This is a global communication done once i.e. we do not track each
        registration individually.

        :param mail_slot: optional <event.mail.slot> slot-specific event communication,
          when event uses slots. In that case, it works like the classic event
          communication (iterative, ...) but information is specific to each
          slot (last registration, scheduled datetime, ...)
        """
        auto_commit = not modules.module.current_test
        batch_size = int(
            self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')
        ) or 50  # be sure to not have 0, as otherwise no iteration is done
        cron_limit = int(
            self.env['ir.config_parameter'].sudo().get_param('mail.render.cron.limit')
        ) or 1000  # be sure to not have 0, as otherwise we will loop
        scheduler_record = mail_slot or self

        # fetch registrations to contact
        registration_domain = [
            ('event_id', '=', self.event_id.id),
            ('state', 'not in', ["draft", "cancel"]),
        ]
        if mail_slot:
            registration_domain += [('event_slot_id', '=', mail_slot.event_slot_id.id)]
        if scheduler_record.last_registration_id:
            registration_domain += [('id', '>', self.last_registration_id.id)]
        registrations = self.env["event.registration"].search(registration_domain, limit=(cron_limit + 1), order="id ASC")

        # no registrations -> done
        if not registrations:
            scheduler_record.mail_done = True
            return

        # there are more than planned for the cron -> reschedule
        if len(registrations) > cron_limit:
            registrations = registrations[:cron_limit]
            self.env.ref('event.event_mail_scheduler')._trigger()

        for registrations_chunk in tools.split_every(batch_size, registrations.ids, self.env["event.registration"].browse):
            self._execute_event_based_for_registrations(registrations_chunk)
            scheduler_record.last_registration_id = registrations_chunk[-1]

            self._refresh_mail_count_done(mail_slot=mail_slot)
            if auto_commit:
                self.env.cr.commit()
                # invalidate cache, no need to keep previous content in memory
                self.env.invalidate_all()