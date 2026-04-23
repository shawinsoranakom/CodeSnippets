def _routing_handle_bounce(self, email_message, message_dict):
        """ Handle bounce of incoming email. Based on values of the bounce (email
        and related partner, send message and its messageID)

          * find blacklist-enabled records with email_normalized = bounced email
            and call ``_message_receive_bounce`` on each of them to propagate
            bounce information through various records linked to same email;
          * if not already done (i.e. if original record is not blacklist enabled
            like a bounce on an applicant), find record linked to bounced message
            and call ``_message_receive_bounce``;

        :param email_message: incoming email;
        :type email_message: email.message;
        :param message_dict: dictionary holding already-parsed values and in
            which bounce-related values will be added;
        :type message_dict: dictionary;
        """
        bounced_record, bounced_record_done = False, False
        bounced_email, bounced_partner = message_dict['bounced_email'], message_dict['bounced_partner']
        bounced_msg_ids, bounced_message = message_dict['bounced_msg_ids'], message_dict['bounced_message']

        if bounced_email:
            bounced_model, bounced_res_id = bounced_message.model, bounced_message.res_id

            if bounced_model and bounced_model in self.env and bounced_res_id:
                bounced_record = self.env[bounced_model].sudo().browse(bounced_res_id).exists()

            bl_models = self.env['ir.model'].sudo().search(['&', ('is_mail_blacklist', '=', True), ('model', '!=', 'mail.thread.blacklist')])
            for model in [bl_model for bl_model in bl_models if bl_model.model in self.env]:  # transient test mode
                rec_bounce_w_email = self.env[model.model].sudo().search([('email_normalized', '=', bounced_email)])
                rec_bounce_w_email._message_receive_bounce(bounced_email, bounced_partner)
                bounced_record_done = bounced_record_done or (bounced_record and model.model == bounced_model and bounced_record in rec_bounce_w_email)

            # set record as bounced unless already done due to blacklist mixin
            if bounced_record and not bounced_record_done and isinstance(bounced_record, self.pool['mail.thread']):
                bounced_record._message_receive_bounce(bounced_email, bounced_partner)

            if bounced_message and (bounced_email or bounced_partner):
                domain = Domain('mail_message_id', '=', bounced_message.id)
                sub_domains = []
                if bounced_partner:
                    sub_domains.append(Domain('res_partner_id', 'in', bounced_partner.ids))
                if bounced_email:
                    sub_domains.append(Domain('mail_email_address', '=', bounced_email))
                self.env['mail.notification'].sudo().search(domain & Domain.OR(sub_domains)).write({
                    'failure_reason': html2plaintext(message_dict.get('body') or ''),
                    'failure_type': 'mail_bounce',
                    'notification_status': 'bounce',
                })

        if bounced_record:
            _logger.info('Routing mail from %s to %s with Message-Id %s: not routing bounce email from %s replying to %s (model %s ID %s)',
                         message_dict['email_from'], message_dict['to'], message_dict['message_id'], bounced_email, bounced_msg_ids, bounced_model, bounced_res_id)
        elif bounced_email:
            _logger.info('Routing mail from %s to %s with Message-Id %s: not routing bounce email from %s replying to %s (no document found)',
                         message_dict['email_from'], message_dict['to'], message_dict['message_id'], bounced_email, bounced_msg_ids)
        else:
            _logger.info('Routing mail from %s to %s with Message-Id %s: not routing bounce email.',
                         message_dict['email_from'], message_dict['to'], message_dict['message_id'])