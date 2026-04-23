def _get_blacklist_record_ids(self, mail_values_dict, recipients_info=None):
        blacklisted_rec_ids = set()
        if not self.use_exclusion_list:
            return blacklisted_rec_ids
        if self.composition_mode == 'mass_mail':
            self.env['mail.blacklist'].flush_model(['email', 'active'])
            self.env.cr.execute("SELECT email FROM mail_blacklist WHERE active=true")
            blacklist = {x[0] for x in self.env.cr.fetchall()}
            if not blacklist:
                return blacklisted_rec_ids
            if isinstance(self.env[self.model], self.pool['mail.thread.blacklist']):
                targets = self.env[self.model].browse(mail_values_dict.keys())
                targets.fetch(['email_normalized'])
                # First extract email from recipient before comparing with blacklist
                blacklisted_rec_ids.update(target.id for target in targets
                                           if target.email_normalized in blacklist)
            elif recipients_info:
                # Note that we exclude the record if at least one recipient is blacklisted (-> even if not all)
                # But as commented above: Mass mailing should always have a single recipient per record.
                blacklisted_rec_ids.update(res_id for res_id, recipient_info in recipients_info.items()
                                           if blacklist & set(recipient_info['mail_to_normalized']))
        return blacklisted_rec_ids