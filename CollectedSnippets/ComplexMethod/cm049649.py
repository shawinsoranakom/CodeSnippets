def l10n_hr_edi_mer_action_fetch_status(self):
        """
        Fetch and update the status of a single document on MojEracun.
        """
        self.ensure_one()
        if self.is_sale_document():
            response_mer = _mer_api_query_document_process_status_outbox(self.company_id, electronic_id=self.l10n_hr_mer_document_eid)[0]
            response_fisc = _mer_api_check_fiscalization_status_outbox(self.company_id, electronic_id=self.l10n_hr_mer_document_eid)
            if isinstance(response_fisc, list):
                response_fisc = {} if len(response_fisc) == 0 else response_fisc[0]
        elif self.is_purchase_document():
            response_mer = _mer_api_query_document_process_status_inbox(self.company_id, electronic_id=self.l10n_hr_mer_document_eid)[0]
            response_fisc = _mer_api_check_fiscalization_status_inbox(self.company_id, electronic_id=self.l10n_hr_mer_document_eid)
            if isinstance(response_fisc, list):
                response_fisc = {} if len(response_fisc) == 0 else response_fisc[0]
        else:
            return
        write_dict = {
            'mer_document_status': str(response_mer.get('StatusId')),
            'business_document_status': str(response_mer.get('DocumentProcessStatusId')),
        }
        if response_fisc:
            write_dict.update({
                'fiscalization_status': str(response_fisc['messages'][-1].get('status')),
                'fiscalization_error': str(response_fisc['messages'][-1].get('errorCode') + ' - ' + response_fisc['messages'][-1].get('errorCodeDescription')),
                'fiscalization_request': str(response_fisc['messages'][-1].get('fiscalizationRequestId')),
                'business_status_reason': str(response_fisc['messages'][-1].get('businessStatusReason')),
                'fiscalization_channel_type': str(response_fisc.get('channelType')),
            })
        self.l10n_hr_edi_addendum_id.write(write_dict)