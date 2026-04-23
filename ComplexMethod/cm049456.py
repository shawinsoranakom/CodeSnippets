def _action_send_sms_mass(self, records=None):
        records = records if records is not None else self._get_records()

        sms_record_values_filtered = self._filter_out_and_handle_revoked_sms_values(self._prepare_mass_sms_values(records))
        records_filtered = records.filtered(lambda record: record.id in sms_record_values_filtered)
        if self.mass_keep_log and sms_record_values_filtered and isinstance(records_filtered, self.pool['mail.thread']):
            log_values = self._prepare_mass_log_values(records_filtered, sms_record_values_filtered)
            mail_messages = records_filtered._message_log_batch(**log_values)
            for idx, record in enumerate(records_filtered):
                sms_record_values_filtered[record.id]['mail_message_id'] = mail_messages[idx].id
        sms_all = self._prepare_mass_sms(records_filtered, sms_record_values_filtered)

        if sms_all and self.mass_force_send:
            sms_all.filtered(lambda sms: sms.state == 'outgoing').send(raise_exception=False)
            return self.env['sms.sms'].sudo().search([('id', 'in', sms_all.ids)])
        return sms_all