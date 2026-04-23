def _l10n_hu_edi_process_query_transaction_result(self, processing_result, annulment_status):
        def get_errors_from_processing_result(processing_result):
            return [
                f'({message["validation_result_code"]}) {message["validation_error_code"]}: {message["message"]}'
                for message in processing_result.get('business_validation_messages', []) + processing_result.get('technical_validation_messages', [])
            ]

        self.ensure_one()

        if processing_result['invoice_status'] in ['RECEIVED', 'PROCESSING', 'SAVED']:
            # The invoice/annulment has not been processed yet.
            if self.l10n_hu_edi_state in ['sent', 'send_timeout']:
                self.write({
                    'l10n_hu_edi_state': 'sent',
                    'l10n_hu_edi_messages': {
                        'error_title': _('The invoice was received by the NAV, but has not been confirmed yet.'),
                        'errors': get_errors_from_processing_result(processing_result),
                        'blocking_level': 'warning',
                    },
                })
            elif self.l10n_hu_edi_state in ['cancel_sent', 'cancel_timeout']:
                self.write({
                    'l10n_hu_edi_state': 'cancel_sent',
                    'l10n_hu_edi_messages': {
                        'error_title': _('The annulment request was received by the NAV, but has not been confirmed yet.'),
                        'errors': get_errors_from_processing_result(processing_result),
                        'blocking_level': 'warning',
                    },
                })

        elif processing_result['invoice_status'] == 'DONE':
            if self.l10n_hu_edi_state in ['sent', 'send_timeout']:
                if not processing_result['business_validation_messages'] and not processing_result['technical_validation_messages']:
                    self.write({
                        'l10n_hu_edi_state': 'confirmed',
                        'l10n_hu_edi_messages': {
                            'error_title': _('The invoice was successfully accepted by the NAV.'),
                            'errors': get_errors_from_processing_result(processing_result),
                        },
                    })
                else:
                    self.write({
                        'l10n_hu_edi_state': 'confirmed_warning',
                        'l10n_hu_edi_messages': {
                            'error_title': _(
                                'The invoice was accepted by the NAV, but warnings were reported. '
                                'To reverse, create a credit note / debit note.'
                            ),
                            'errors': get_errors_from_processing_result(processing_result),
                            'blocking_level': 'warning',
                        },
                    })
            elif self.l10n_hu_edi_state in ['cancel_sent', 'cancel_timeout', 'cancel_pending']:
                if annulment_status == 'NOT_VERIFIABLE':
                    self.write({
                        'l10n_hu_edi_state': 'confirmed_warning',
                        'l10n_hu_edi_messages': {
                            'error_title': _('The annulment request was rejected by NAV.'),
                            'errors': get_errors_from_processing_result(processing_result),
                            'blocking_level': 'error',
                        },
                    })
                elif annulment_status == 'VERIFICATION_PENDING':
                    self.write({
                        'l10n_hu_edi_state': 'cancel_pending',
                        'l10n_hu_edi_messages': {
                            'error_title': _('The annulment request is pending, please confirm it on the OnlineSzámla portal.'),
                            'errors': get_errors_from_processing_result(processing_result),
                            'blocking_level': 'warning',
                        }
                    })
                elif annulment_status == 'VERIFICATION_DONE':
                    # Annulling a base invoice will also annul all its modification invoices on NAV.
                    to_cancel = self if self.reversed_entry_id or self.debit_origin_id else self._l10n_hu_get_chain_invoices().filtered(lambda m: m.l10n_hu_edi_state)
                    to_cancel.write({
                        'l10n_hu_edi_state': 'cancelled',
                        'l10n_hu_invoice_chain_index': 0,
                        'l10n_hu_edi_messages': {
                            'error_title': _('The annulment request has been approved by the user on the OnlineSzámla portal.'),
                            'errors': get_errors_from_processing_result(processing_result),
                        }
                    })
                    to_cancel.button_cancel()
                elif annulment_status == 'VERIFICATION_REJECTED':
                    self.write({
                        'l10n_hu_edi_state': 'confirmed_warning',
                        'l10n_hu_edi_messages': {
                            'error_title': _('The annulment request was rejected by the user on the OnlineSzámla portal.'),
                            'errors': get_errors_from_processing_result(processing_result),
                            'blocking_level': 'error',
                        }
                    })

        elif processing_result['invoice_status'] == 'ABORTED':
            if self.l10n_hu_edi_state in ['sent', 'send_timeout']:
                self.write({
                    'l10n_hu_edi_state': 'rejected',
                    'l10n_hu_invoice_chain_index': 0,
                    'l10n_hu_edi_messages': {
                        'error_title': _('The invoice was rejected by the NAV.'),
                        'errors': get_errors_from_processing_result(processing_result),
                        'blocking_level': 'error',
                    },
                })
            elif self.l10n_hu_edi_state in ['cancel_sent', 'cancel_timeout', 'cancel_pending']:
                self.write({
                    'l10n_hu_edi_state': 'confirmed_warning',
                    'l10n_hu_edi_messages': {
                        'error_title': _('The cancellation request could not be performed.'),
                        'errors': get_errors_from_processing_result(processing_result),
                        'blocking_level': 'error',
                    },
                })