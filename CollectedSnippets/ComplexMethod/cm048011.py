def _send_as_batch(self):
        # Documents in `self` should all belong to `self.env.company`.
        # For the cron we specifically set the `self.env.company` on some functions we call.
        sender_company = self.env.company

        batch_errors = self.with_company(sender_company)._send_as_batch_check()
        if batch_errors:
            error_title = _("The batch document could not be created")
            self.errors = self._format_errors(error_title, batch_errors)
            info = {'errors': batch_errors}
            return None, info

        # When the document is sent more than 240s after its creation the AEAT registers the document only with an error
        # See error with code 2004:
        #   El valor del campo FechaHoraHusoGenRegistro debe ser la fecha actual del sistema de la AEAT,
        #   admitiéndose un margen de error de: 240 segundos.
        incident = any(document.create_date > fields.Datetime.now() + timedelta(seconds=240) for document in self)

        document_dict_list = [document._get_document_dict() for document in self]
        batch_dict = self.with_company(sender_company)._get_batch_dict(document_dict_list, incident=incident)

        info = self.with_company(sender_company)._send_batch(batch_dict)

        batch_failure_info = {}
        if info['soap_fault'] or info['errors']:
            # Handle SOAP fault or the case that something went wrong while sending or parsing the respone.
            batch_failure_info = {
                'errors': info['errors'],
                'state': 'rejected' if info['soap_fault'] else False
            }

        # Store the information from the response split over the individual documents
        for document, document_dict in zip(self, document_dict_list):
            response_info = (
                batch_failure_info
                or info['record_info'].get(self._extract_record_key(document_dict), None)
                or {'errors': [_("We could not find any information about the record in the linked batch document.")]}
            )

            # In case of a timeout the document may have reached the AEAT but
            # we have not received the response. That is why we take the
            # duplicate information in case of timeout.
            duplicate_info = response_info.get('duplicate', {})
            if (not document.state
                and duplicate_info
                and document.errors
                and "[Read-Timeout] " in document.errors):
                if document.document_type == 'submission' and duplicate_info['state'] in ('accepted', 'registered_with_errors'):
                    response_info.update({
                        'state': duplicate_info['state'],
                        'errors': duplicate_info['errors'],
                    })
                elif document.document_type == 'cancellation' and duplicate_info['state'] == 'cancelled':
                    response_info.update({
                        'state': 'accepted',
                        'errors': duplicate_info['errors'],
                    })

            # Add some information from the batch level in any case.
            response_info.update({
                'waiting_time_seconds': info.get('waiting_time_seconds', False),
                'response_csv': info.get('response_csv', False),
            })

            # The errors have to be formatted (as HTML) before storing them on the document
            errors_html = False
            error_list = response_info.get('errors', [])
            if error_list:
                error_title = _("Error")
                if response_info.get('state', False):
                    error_title = _("The Veri*Factu document contains the following errors according to the AEAT")
                errors_html = self._format_errors(error_title, error_list)
            document.errors = errors_html

            # All other values can be stored directly on the document
            keys = ['response_csv', 'state']
            for key in keys:
                new_value = response_info.get(key, False)
                if new_value or document[key]:
                    document[key] = new_value

            # To avoid losing data we commit after every document
            if self.env['account.move']._can_commit():
                self.env.cr.commit()

        waiting_time_seconds = info.get('waiting_time_seconds')
        if waiting_time_seconds:
            now = fields.Datetime.to_datetime(fields.Datetime.now())
            next_batch_time = now + timedelta(seconds=waiting_time_seconds)
            self.env.company.l10n_es_edi_verifactu_next_batch_time = next_batch_time

        self._cancel_after_sending(info)

        if self.env['account.move']._can_commit():
            self.env.cr.commit()

        return batch_dict, info