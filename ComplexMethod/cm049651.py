def _l10n_hr_mer_get_new_documents(self, undelivered_only=True, slc=False, from_cron=False):
        """
        Import documents from MojEracun. Additional arguments included for testing.
        :param undelivered_only (bool, optional): Import only undelivered documents. Defaults to True.
        :param slc (tuple of two ints, optional): Import only a slice of the list of documents for testing. Defaults to False.
        """
        job_count = self.env.context.get('mer_crons_job_count') or BATCH_SIZE
        need_retrigger = False
        imported_documents = {}
        for company in self.filtered(lambda c: c.l10n_hr_mer_connection_state == 'active'):
            try:
                response = _mer_api_query_inbox(company, 'Undelivered' if undelivered_only else None)
            except MojEracunServiceError as e:
                _logger.error('MojEracun service error: %s', e.message)
                continue

            error = False
            if isinstance(response, list):
                if not len(response):
                    # Case 1: empty list - no documents in the inbox
                    _logger.info("MojEracun inbox is empty for company: %s", company.name)
                    continue
                elif any(not (item.get('ElectronicId') and item.get('StatusId')) for item in response):
                    # Case 2: a list with elements that appear to not be valid document dicts
                    error = ("Incorrect multiple document response format while querying inbox for company: %(company)s: %(response)s",
                             company.name, response)
                else:
                    # Case 3: a list of valid document dicts
                    pass
            elif isinstance(response, dict):
                if not (response.get('ElectronicId') and response.get('StatusId')):
                    # Case 4: a single dict that doesn't appear to be a valid document
                    error = ("Incorrect single document response format while querying inbox for company: %(company)s: %(response)s",
                             company.name, response)
                else:
                    # Case 5: a single valid document dict
                    response = [response]
            else:
                # Case 6: unrecognizeable response
                error = ("Incorrect response format while querying inbox for company: %s", company.name)
            if error:
                if from_cron:
                    _logger.error("MojEracun service error: %s", error)
                    continue
                else:
                    raise MojEracunServiceError('service_error', error)
            documents = [{'mer_document_eid': str(document['ElectronicId']), 'mer_document_status': str(document['StatusId'])} for document in response][::-1]
            if not documents:
                continue

            need_retrigger = need_retrigger or len(documents) > job_count
            documents = documents[:job_count]

            existing_documents = self.env['l10n_hr_edi.addendum'].search([
                ("mer_document_eid", "in", [i['mer_document_eid'] for i in documents]),
                ('move_id.company_id', '=', company.id)])
            documents_to_import = [i for i in documents if i['mer_document_eid'] not in existing_documents.mapped('mer_document_eid')]
            proxy_acks = []
            # Retrieve attachments for the document IDs received
            if slc:
                documents_to_import = documents_to_import[slc[0]:slc[1]]
            for document in documents_to_import:
                try:
                    fisc_data = _mer_api_check_fiscalization_status_inbox(company, electronic_id=document['mer_document_eid'])
                    if fisc_data == []:
                        _logger.info("Fiscalization data for document eID %s is not available on MojEracun server.", document['mer_document_eid'])
                    else:
                        fisc_data = fisc_data[0]
                except (MojEracunServiceError, UserError):
                    _logger.error("Failed to retreive fisc data for document eID %s", document['mer_document_eid'])
                    if from_cron:
                        continue
                    elif company.l10n_hr_mer_connection_mode == 'test':
                        # Bypassing randomness of MER test server responce
                        fisc_data = {'messages': [{
                                'status': '0',
                                'errorCode': None,
                                'errorCodeDescription': 'Nema greške',
                                'fiscalizationRequestId': '00001-test',
                                'businessStatusReason': None,
                            }],
                            'channelType': '0',
                        }
                    else:
                        raise
                if fisc_data:
                    document.update({
                        'fiscalization_status': str(fisc_data['messages'][-1].get('status')),
                        'fiscalization_error': str(fisc_data['messages'][-1].get('errorCode')) + ' - ' + str(fisc_data['messages'][-1].get('errorCodeDescription')),
                        'fiscalization_request': str(fisc_data['messages'][-1].get('fiscalizationRequestId')),
                        'business_status_reason': str(fisc_data['messages'][-1].get('businessStatusReason')),
                        'fiscalization_channel_type': str(fisc_data.get('channelType')),
                    })
                    if document['fiscalization_status'] != '0':
                        _logger.warning("Document eID %s is not successfully fiscalized by MojEracun.", document['mer_document_eid'])
                try:
                    business_data = _mer_api_query_document_process_status_inbox(company, electronic_id=document['mer_document_eid'])[0]
                except (MojEracunServiceError, UserError):
                    _logger.error("Failed to retreive business data for document: %s", document['mer_document_eid'])
                    if from_cron:
                        continue
                    elif company.l10n_hr_mer_connection_mode == 'test':
                        # Bypassing randomness of MER test server responce
                        business_data = {
                            'DocumentProcessStatusId': '0',
                        }
                    else:
                        raise
                document.update({
                    'business_document_status': str(business_data.get('DocumentProcessStatusId')),
                })
                try:
                    document_xml = _mer_api_receive_document(company, document['mer_document_eid'])
                except MojEracunServiceError as e:
                    _logger.error("Failed to retrieve document: %s", e.message)
                    continue

                attachment = self.env["ir.attachment"].create(
                    {
                        "name": f"mojeracun_{document['mer_document_eid']}_attachment.xml",
                        "raw": document_xml,
                        "type": "binary",
                        "mimetype": "application/xml",
                    }
                )
                if self._l10n_hr_mer_import_invoice(attachment, document):
                    # Only acknowledge on successful import
                    proxy_acks.append(document['mer_document_eid'])
                if not tools.config['test_enable']:
                    self.env.cr.commit()
                    _mer_api_notify_import(company, document['mer_document_eid'])

            imported_documents.update({company.id: proxy_acks})
        if need_retrigger:
            self.env.ref('l10n_hr_edi.ir_cron_mer_get_new_documents')._trigger()
        # Return the documents that were successfully imported
        return imported_documents