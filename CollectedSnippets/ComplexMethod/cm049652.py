def _l10n_hr_mer_fetch_document_status_company(self, from_cron=False):
        """
        Fetch and update the status of up to 20000 documents belonging to a company on MojEracun.
        """
        for company in self.filtered(lambda c: c.l10n_hr_mer_connection_state == 'active'):
            for query_function, check_function in [
                (_mer_api_query_document_process_status_outbox, _mer_api_check_fiscalization_status_outbox),
                (_mer_api_query_document_process_status_inbox, _mer_api_check_fiscalization_status_inbox)
            ]:
                response_mer = query_function(company, by_update_date=True)
                documents = {
                    str(item['ElectronicId']): {
                        'mer_document_status': str(item.get('StatusId')),
                        'business_document_status': str(item.get('DocumentProcessStatusId')),
                    } for item in response_mer
                }
                try:
                    response_fisc = check_function(company)
                except (MojEracunServiceError, UserError):
                    _logger.error("Failed to retreive fiscalization data for company %s", company.name)
                    if from_cron or company.l10n_hr_mer_connection_mode == 'test':
                        response_fisc = []
                    else:
                        raise
                for item in response_fisc:
                    # As we can't fetch all the data with a single query, it's either this or making calls move-by-move
                    # Currently, because of the random nature of responses received from fisc endpoints, this breaks tests
                    if item.get('ElectronicId') in documents:
                        documents[item['ElectronicId']].update({
                            'fiscalization_status': str(item['messages'][-1].get('status')),
                            'fiscalization_error': str(item['messages'][-1].get('errorCode')) + ' - ' + str(item['messages'][-1].get('errorCodeDescription')),
                            'fiscalization_request': str(item['messages'][-1].get('fiscalizationRequestId')),
                            'business_status_reason': str(item['messages'][-1].get('fiscalizationRequestId')),
                            'fiscalization_channel_type': str(item.get('channelType')),
                        })
                addendums = self.env['l10n_hr_edi.addendum'].search([
                    ("mer_document_eid", "in", list(documents.keys())),
                    ('move_id.company_id', '=', company.id),
                ])
                for addendum in addendums:
                    addendum.write(documents[addendum.mer_document_eid])