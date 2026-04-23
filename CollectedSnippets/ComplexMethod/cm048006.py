def _create_for_record(self, record_values):
        """Create Veri*Factu documents for input `record_values`.
        Return the created document.
        The documents are also created in case the JSON generation fails; to inspect the errors.
        Such documents are deleted in case the JSON generation succeeds for a record at a later time.
        (In case we succesfully create a JSON we delete all linked documents that failed the JSON creation.)
        :param list record_values: record values dictionary
        """
        document_vals = record_values['document_vals']
        error_title = _("The Veri*Factu document could not be created")

        if not record_values['errors']:
            record_values['errors'] = self._check_record_values(record_values)

        if record_values['errors']:
            document_vals['errors'] = self._format_errors(error_title, record_values['errors'])
        else:
            previous_document = record_values['company']._l10n_es_edi_verifactu_get_last_document()
            render_vals = self._render_vals(
                record_values, previous_record_identifier=previous_document._get_record_identifier(),
            )
            document_dict = {render_vals['record_type']: render_vals[render_vals['record_type']]}

            # We check whether zeep can generate a valid XML (according to the information from the WSDL / XSD)
            # from the `document_dict`.
            # Otherwise this may happen at sending. But then the issue may be hard to resolve:
            # - Each generated document should also be sent to the AEAT.
            # - Documents must not be altered after generation.
            # The created XML (`create_message`) is just discarded.
            create_message = None
            try:
                # We only generate the XML; nothing is sent at this point.
                create_message, _zeep_info = _get_zeep_operation(record_values['company'], 'registration_xml')
            except (zeep.exceptions.Error, requests.exceptions.RequestException) as error:
                # The zeep client creation may cause a networking error
                errors = [_("Networking error: %s", error)]
                document_vals['errors'] = self._format_errors(error_title, errors)
                _logger.error("%s\n%s\n%s", error_title, errors[0], json.dumps(document_dict, indent=4))

            if create_message:
                batch_dict = self.with_company(record_values['company'])._get_batch_dict([document_dict])
                try:
                    _xml_node = create_message(batch_dict['Cabecera'], batch_dict['RegistroFactura'])
                except zeep.exceptions.ValidationError as error:
                    errors = [_("Validation error: %s", error)]
                    document_vals['errors'] = self._format_errors(error_title, errors)
                    _logger.error("%s\n%s\n%s", error_title, errors[0], json.dumps(batch_dict, indent=4))
                except zeep.exceptions.Error as error:
                    errors = [error]
                    document_vals['errors'] = self._format_errors(error_title, errors)
                    _logger.error("%s\n%s\n%s", error_title, errors[0], json.dumps(batch_dict, indent=4))

            if not document_vals.get('errors'):
                chain_sequence = record_values['company'].sudo()._l10n_es_edi_verifactu_get_chain_sequence()
                try:
                    document_vals['chain_index'] = chain_sequence.next_by_id()
                except OperationalError as e:
                    # We chain all the created documents per company in generation order.
                    # (indexed by `chain_index`).
                    # Thus we can not generate multiple documents for the same company at the same time.
                    # Function `next_by_id` effectively locks `company.l10n_es_edi_verifactu_chain_sequence_id`
                    # to prevent different transactions from chaining documents at the same time.
                    errors = [_("Error while chaining the document: %s", e)]
                    document_vals['errors'] = self._format_errors(error_title, errors)
                    _logger.error("%s\n%s\n%s", error_title, errors[0], json.dumps(batch_dict, indent=4))

        document = self.sudo().create(document_vals)

        if document.chain_index:
            attachment = self.env['ir.attachment'].sudo().create({
                'raw': json.dumps(document_dict, indent=4).encode(),
                'name': document.json_attachment_filename,
                'res_id': document.id,
                'res_model': document._name,
                'mimetype': 'application/json',
            })
            document.sudo().json_attachment_id = attachment
            # Remove (previously generated) documents that failed to generate a (valid) JSON
            record_values['documents'].filtered(lambda rd: not rd.json_attachment_id).sudo().unlink()

        return document