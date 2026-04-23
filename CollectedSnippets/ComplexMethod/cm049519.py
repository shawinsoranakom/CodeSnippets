def _nemhandel_get_new_documents(self, skip_no_journal=True, batch_size=None):
        job_count = batch_size or BATCH_SIZE
        need_retrigger = False
        params = {
            'domain': {
                'direction': 'incoming',
                'errors': False,
            }
        }
        for edi_user in self:
            edi_user = edi_user.with_company(edi_user.company_id)
            journal = edi_user.company_id.nemhandel_purchase_journal_id
            if not journal:
                msg = _('Please set a journal for Nemhandel invoices on %s before receiving documents.', edi_user.company_id.display_name)
                if skip_no_journal:
                    _logger.warning(msg)
                else:
                    raise UserError(msg)

            params['domain']['receiver_identifier'] = edi_user.edi_identification
            try:
                # request all messages that haven't been acknowledged
                messages = edi_user._call_nemhandel_proxy(
                    "/api/nemhandel/1/get_all_documents",
                    params=params,
                )
            except UserError as e:
                _logger.error(
                    'Error while receiving the document from Nemhandel Proxy: %s', ', '.join(e.args),
                )
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
            all_messages = edi_user._call_nemhandel_proxy(
                "/api/nemhandel/1/get_document",
                params={'message_uuids': message_uuids},
            )

            processed_uuids, moves = edi_user._nemhandel_process_new_messages(all_messages)

            if not (modules.module.current_test or tools.config['test_enable']):
                self.env.cr.commit()
            if processed_uuids:
                edi_user._call_nemhandel_proxy(
                    "/api/nemhandel/1/ack",
                    params={'message_uuids': processed_uuids},
                )
                edi_user._nemhandel_post_process_new_messages(moves)
        if need_retrigger:
            self.env.ref('l10n_dk_nemhandel.ir_cron_nemhandel_get_new_documents')._trigger()