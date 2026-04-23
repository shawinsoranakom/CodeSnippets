def _remove(self, numbers, message=None):
        """ Add de-activated or de-activate a phone blacklist entry.

        :param numbers: list of sanitized numbers """
        records = self.env["phone.blacklist"].with_context(active_test=False).search([('number', 'in', numbers)])
        todo = [n for n in numbers if n not in records.mapped('number')]
        if records:
            if message:
                records._track_set_log_message(message)
            records.action_archive()
        if todo:
            new_records = self.create([{'number': n, 'active': False} for n in todo])
            if message:
                for record in new_records:
                    record.with_context(mail_post_autofollow_author_skip=True).message_post(
                        body=message,
                        subtype_xmlid='mail.mt_note',
                    )
            records += new_records
        return records