def _message_sms(self, body, subtype_id=False, partner_ids=False, number_field=False,
                     sms_numbers=None, sms_pid_to_number=None, **kwargs):
        """ Main method to post a message on a record using SMS-based notification
        method.

        :param body: content of SMS;
        :param subtype_id: mail.message.subtype used in mail.message associated
          to the sms notification process;
        :param partner_ids: if set is a record set of partners to notify;
        :param number_field: if set is a name of field to use on current record
          to compute a number to notify;
        :param sms_numbers: see ``_notify_thread_by_sms``;
        :param sms_pid_to_number: see ``_notify_thread_by_sms``;
        """
        self.ensure_one()
        sms_pid_to_number = sms_pid_to_number if sms_pid_to_number is not None else {}

        if number_field or (partner_ids is False and sms_numbers is None):
            info = self._sms_get_recipients_info(force_field=number_field)[self.id]
            info_partner_ids = info['partner'].ids if info['partner'] else False
            info_number = info['sanitized'] if info['sanitized'] else info['number']
            if info_partner_ids and info_number:
                sms_pid_to_number[info_partner_ids[0]] = info_number
            if info_partner_ids:
                partner_ids = info_partner_ids + (partner_ids or [])
            if not info_partner_ids:
                if info_number:
                    sms_numbers = [info_number] + (sms_numbers or [])
                    # will send a falsy notification allowing to fix it through SMS wizards
                elif not sms_numbers:
                    sms_numbers = [False]

        if subtype_id is False:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        return self.message_post(
            body=body, partner_ids=partner_ids or [],  # TDE FIXME: temp fix otherwise crash mail_thread.py
            message_type='sms', subtype_id=subtype_id,
            sms_numbers=sms_numbers, sms_pid_to_number=sms_pid_to_number,
            **kwargs
        )