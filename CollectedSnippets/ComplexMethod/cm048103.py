def _l10n_gr_edi_handle_send_result(self, result, xml_vals):
        """
        Handle the result object received from sending xml to myDATA.
        Create the related error/sent document with the necessary values.
        """
        move_xml_map = {}  # Dictionary mapping of ``move_id`` -> ``xml_content``.
        for invoice_vals in xml_vals['invoice_values_list']:
            single_xml_vals = {'invoice_values_list': [invoice_vals]}
            move = invoice_vals['__move__']
            xml_template = 'l10n_gr_edi.mydata_invoice' if move.is_sale_document(include_receipts=True) else 'l10n_gr_edi.mydata_expense_classification'
            xml_content = self._l10n_gr_edi_generate_xml_content(xml_template, single_xml_vals)
            move_xml_map[move] = xml_content

        move_ids = list(move_xml_map.keys())

        if 'error' in result:
            # If the request failed at this stage, it is probably caused by connection/credentials issues.
            # In such case, we don't need to attach the xml here as it won't be helpful for the user.
            for move in move_ids:
                move._l10n_gr_edi_create_error_document(result)
        else:
            for result_id, result_dict in result.items():
                move = move_ids[result_id]
                xml_content = move_xml_map[move]
                document_values = {**result_dict, 'xml_content': xml_content}
                # Delete previous error documents
                move.l10n_gr_edi_document_ids.filtered(lambda d: d.state in ('invoice_error', 'bill_error')).unlink()
                if 'error' in result_dict:
                    # In this stage, the sending process has succeeded, and any error we receive is generated from the myDATA API.
                    # Previous error(s) without attachments (generated from pre-compute) are now useless and can be unlinked.
                    move._l10n_gr_edi_create_error_document(document_values)
                else:
                    move._l10n_gr_edi_create_sent_document(document_values)

        if self._can_commit():
            self.env.cr.commit()