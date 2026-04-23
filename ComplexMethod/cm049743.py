def _action_send_mail_mass_mail(self, res_ids, auto_commit=False):
        """ Send in mass mail mode. Mails are sudo-ed, as when going through
        _prepare_mail_values standard access rights on related records will be
        checked when browsing them to compute mail values. If people have
        access to the records they have rights to create lots of emails in
        sudo as it is considered as a technical model. """
        mails_sudo = self.env['mail.mail'].sudo()

        batch_size = int(
            self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')
        ) or self._batch_size or 50  # be sure to not have 0, as otherwise no iteration is done
        counter_mails_done = 0
        for res_ids_iter in tools.split_every(batch_size, res_ids):
            prepared_mail_values_filtered = self._manage_mail_values(self._prepare_mail_values(res_ids_iter))
            iter_mails_sudo = self.env['mail.mail'].sudo().create(list(prepared_mail_values_filtered.values()))
            self.env['mail.notification'].create(self._generate_mail_notification_values(iter_mails_sudo))
            mails_sudo += iter_mails_sudo

            records = self.env[self.model].browse(prepared_mail_values_filtered.keys()) if self.model and hasattr(self.env[self.model], 'message_post') else False
            if records:
                records._message_mail_after_hook(iter_mails_sudo)

            if self.force_send:
                # as 'send' does not filter out scheduled mails (only 'process_email_queue'
                # does) we need to do it manually
                iter_mails_sudo_tosend = iter_mails_sudo.filtered(
                    lambda mail: (
                        not mail.scheduled_date or
                        mail.scheduled_date <= datetime.datetime.utcnow()
                    )
                )
                if iter_mails_sudo_tosend:
                    iter_mails_sudo_tosend.send(auto_commit=auto_commit)
                    continue
            # sending emails will commit and invalidate cache; in case we do not force
            # send better void the cache and commit what is already generated to avoid
            # running several times on same records in case of issue
            if auto_commit is True:
                counter_mails_done += len(prepared_mail_values_filtered)
                self.env['ir.cron']._notify_progress(done=counter_mails_done,
                                                      remaining=len(res_ids) - counter_mails_done)
                self.env.cr.commit()
            self.env.invalidate_all()

        return mails_sudo