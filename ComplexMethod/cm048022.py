def _peppol_get_message_status(self):
        # Context added to not break stable policy: useful to tweak on databases processing large invoices
        job_count = self.env.context.get('peppol_crons_job_count') or BATCH_SIZE
        need_retrigger = False
        for edi_user in self:
            edi_user = edi_user.with_company(edi_user.company_id)
            documents = edi_user._peppol_get_documents_for_status(job_count)
            if not documents:
                continue
            need_retrigger = need_retrigger or len(documents) > job_count
            uuid_to_record = {document.peppol_message_uuid: document for document in documents[:job_count]}
            messages_to_process = edi_user._call_peppol_proxy(
                "/api/peppol/1/get_document",
                params={'message_uuids': list(uuid_to_record)},
            )

            processed_message_uuids = edi_user._peppol_process_messages_status(messages_to_process, uuid_to_record)

            if processed_message_uuids:
                edi_user._call_peppol_proxy(
                    "/api/peppol/1/ack",
                    params={'message_uuids': processed_message_uuids},
                )
        if need_retrigger:
            self.env.ref('account_peppol.ir_cron_peppol_get_message_status')._trigger(
                fields.Datetime.add(fields.Datetime.now(), minutes=5),
            )