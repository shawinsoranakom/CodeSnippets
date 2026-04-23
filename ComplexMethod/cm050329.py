def _l10n_it_edi_update_send_state(self):
        ''' Check if the current invoices have been processed by the SdI. '''
        proxy_user = self.company_id.l10n_it_edi_proxy_user_id
        if proxy_user.edi_mode == 'demo':
            for move in self:
                filename = move.l10n_it_edi_attachment_name or '???'
                self._l10n_it_edi_write_send_state(
                    transformed_notification={
                        'l10n_it_edi_state': 'forwarded',
                        'l10n_it_edi_transaction': f'demo_{uuid.uuid4()}',
                        'send_ack_to_edi_proxy': False,
                        'date': fields.Date.today(),
                        'filename': filename},
                    message=_("The e-invoice file %s has been sent in Demo EDI mode.", filename))
            return

        server_url = proxy_user._get_server_url()
        try:
            notifications = proxy_user._make_request(
                f'{server_url}/api/l10n_it_edi/1/in/TrasmissioneFatture',
                params={'ids_transaction': self.mapped("l10n_it_edi_transaction")})
        except AccountEdiProxyError as pe:
            raise UserError(_("An error occurred while downloading updates from the Proxy Server: (%(code)s) %(message)s", code=pe.code, message=pe.message)) from pe

        for notification in notifications.values():
            encrypted_update_content = notification.get('file')
            encryption_key = notification.get('key')
            if (encrypted_update_content and encryption_key):
                notification['xml_content'] = proxy_user._decrypt_data(encrypted_update_content, encryption_key)

        acks = {'transaction_ids': [], 'states': []}
        for move in self:
            notification = notifications[move.l10n_it_edi_transaction]
            parsed_notification = move._l10n_it_edi_parse_notification(notification)
            transformed_notification = move._l10n_it_edi_transform_notification(parsed_notification)
            message = move._l10n_it_edi_get_message(transformed_notification)
            move._l10n_it_edi_write_send_state(transformed_notification, message)
            if (
                transformed_notification.get('send_ack_to_edi_proxy')
                and (id_transaction_to_ack := transformed_notification.get('l10n_it_edi_transaction'))
                and (ack_state := transformed_notification.get('l10n_it_edi_state'))
            ):
                acks['transaction_ids'].append(id_transaction_to_ack)
                acks['states'].append(ack_state)

        if acks:
            transaction_ids = acks['transaction_ids']
            states = acks['states']
            try:
                proxy_user._make_request(
                    f'{server_url}/api/l10n_it_edi/1/ack',
                    params={'transaction_ids': transaction_ids, 'states': states})
            except AccountEdiProxyError as pe:
                raise UserError(_("An error occurred while downloading updates from the Proxy Server: (%(code)s) %(message)s", code=pe.code, message=pe.message)) from pe