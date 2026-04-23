def _peppol_get_new_documents(self, skip_no_journal=False):
        # Context added to not break stable policy: useful to tweak on databases processing large invoices
        job_count = self.env.context.get('peppol_crons_job_count') or BATCH_SIZE
        need_retrigger = False
        params = {
            'domain': {
                'direction': 'incoming',
                'errors': False,
            }
        }
        for edi_user in self:
            edi_user = edi_user.with_company(edi_user.company_id)
            if not edi_user.company_id.peppol_purchase_journal_id:
                msg = _('Please set a journal for Peppol invoices on %s before receiving documents.', edi_user.company_id.display_name)
                if skip_no_journal:
                    _logger.warning(msg)
                else:
                    raise UserError(msg)

            params['domain']['receiver_identifier'] = edi_user.edi_identification
            try:
                # request all messages that haven't been acknowledged
                messages = edi_user._call_peppol_proxy(
                    "/api/peppol/1/get_all_documents",
                    params=params,
                )
            except AccountEdiProxyError as e:
                _logger.error(
                    'Error while receiving the document from Peppol Proxy: %s', e.message)
                continue

            message_uuids = [
                message['uuid']
                for message in messages.get('messages', [])
            ]
            if not message_uuids:
                continue

            need_retrigger = need_retrigger or len(message_uuids) > job_count
            message_uuids = message_uuids[:job_count]

            # retrieve attachments for filtered messages
            all_messages = edi_user._call_peppol_proxy(
                "/api/peppol/1/get_document",
                params={'message_uuids': message_uuids},
            )

            processed_uuids, moves = edi_user._peppol_process_new_messages(all_messages)

            if not (modules.module.current_test or tools.config['test_enable']):
                self.env.cr.commit()
            if processed_uuids:
                edi_user._call_peppol_proxy(
                    "/api/peppol/1/ack",
                    params={'message_uuids': processed_uuids},
                )
                edi_user._peppol_post_process_new_messages(moves)

        if need_retrigger:
            self.env.ref('account_peppol.ir_cron_peppol_get_new_documents')._trigger()