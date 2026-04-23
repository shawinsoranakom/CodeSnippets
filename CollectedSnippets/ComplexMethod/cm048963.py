def _myinvois_submit_documents(self, submissions_content):
        """
        Contact our IAP service in order to send the current document's xml to the MyInvois API.
        Only records in self having a xml_file_content in xml_contents will be sent.

        Please mind that the logic will commit for each batch being sent to the platform.

        :param submissions_content: A dict of the format {record: {'name': '', 'xml': ''}}
        :return: a dict of potential errors in the format {record: errors_list}
        """
        def _format_error_messages(errors_list):
            AccountMoveSend = self.env['account.move.send']
            error_data = {
                'error_title': self.env._("Error when sending the documents to the E-invoicing service."),
                'errors': errors_list,
            }
            return {
                'html_error': AccountMoveSend._format_error_html(error_data),
                'plain_text_error': AccountMoveSend._format_error_text(error_data),
            }

        records_to_send = self.filtered(lambda record: record in submissions_content)
        if not records_to_send:
            return None

        # Ensure to lock the records that will be sent, to avoid risking sending them twice.
        self.env['res.company']._with_locked_records(records_to_send)

        error_messages = {}
        success_messages = {}
        invoice_to_cancel = self.env['account.move']

        # We will group per proxy_user, then batch the records in batches of SUBMISSION_MAX_SIZE
        records_per_proxy_users = records_to_send.grouped(lambda r: r._myinvois_get_proxy_user())

        # MyInvois only supports up to 100 document per submission. To avoid timing out on big batches, we split it client side.
        for proxy_user, records_to_send in records_per_proxy_users.items():
            for batch in split_every(SUBMISSION_MAX_SIZE, records_to_send.ids, self.env['myinvois.document'].browse):
                batch_result = proxy_user._l10n_my_edi_contact_proxy(
                    endpoint='api/l10n_my_edi/1/submit_invoices',
                    params={
                        'documents': [{
                            'move_id': record.id,
                            'move_name': submissions_content[record]['name'],
                            'error_document_hash': record.myinvois_error_document_hash,
                            'retry_at': record.myinvois_retry_at,
                            'data': base64.b64encode(submissions_content[record]['xml'].encode()).decode(),
                        } for record in batch],
                    },
                )
                # If an error is present in the result itself (and not per document), it means that the whole submission failed.
                # We don't add to the result but instead directly in the errors.
                if 'error' in batch_result:
                    error_string = self._myinvois_map_error(batch_result['error'])
                    error_messages.update({record.id: _format_error_messages([error_string]) for record in batch})
                else:
                    records_per_id = batch.grouped('id')
                    for document_result in batch_result['documents']:
                        record = records_per_id[document_result['move_id']]
                        success = document_result['success']

                        updated_values = {
                            'myinvois_external_uuid': document_result.get('uuid'),  # rejected documents do not have an uuid.
                            'myinvois_submission_uid': batch_result['submission_uid'],
                            'myinvois_state': 'in_progress' if success else 'invalid',
                        }

                        if success:
                            # Ids are logged for future references. An invalid document may be reset to resend it after correction, which would be a new submission/uuid.
                            success_messages[record.id] = self.env._('The document has been sent to MyInvois with uuid "%(uuid)s" and submission id "%(submission_id)s".\nValidation results will be available shortly.',
                                                                     uuid=document_result['uuid'], submission_id=batch_result['submission_uid'])
                        else:
                            # When we raise a "hash_resubmitted" error, we don't resend the same hash/retry at and don't want to rewrite.
                            if 'error_document_hash' in document_result:
                                updated_values.update({
                                    'myinvois_error_document_hash': document_result['error_document_hash'],
                                    'myinvois_retry_at': document_result['retry_at'],
                                })
                            error_messages[record.id] = _format_error_messages([self._myinvois_map_error(error) for error in document_result['errors']])
                            if self.invoice_ids:
                                invoice_to_cancel |= self.invoice_ids

                        record.write(updated_values)

                if self._can_commit():
                    self.env.cr.commit()

        if success_messages:
            successful_records = self.browse(list(success_messages.keys()))
            successful_records._myinvois_log_message(
                bodies=success_messages,
            )
        if error_messages:
            unsuccessful_records = self.browse(list(error_messages.keys()))
            unsuccessful_records._myinvois_log_message(
                bodies={rid: msg['html_error'] for rid, msg in error_messages.items()},
            )

        if invoice_to_cancel:
            # Invalid moves should be considered as cancelled; they need to be reset to draft, corrected and sent again.
            invoice_to_cancel._l10n_my_edi_cancel_moves()

        return error_messages