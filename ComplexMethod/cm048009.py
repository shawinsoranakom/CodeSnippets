def trigger_next_batch(self):
        """
        1. Send all waiting documents that we can send
        2. Trigger the cron again at a later date to send the documents we could not send
        """
        unsent_domain = [
            ('json_attachment_id', '!=', False),
            ('state', '=', False),
        ]
        documents_per_company = self.sudo()._read_group(
            unsent_domain,
            groupby=['company_id'],
            aggregates=['id:recordset'],
        )

        if not documents_per_company:
            return

        next_trigger_time = None
        for company, documents in documents_per_company:
            # Avoid sending a document twice due to concurrent calls to `trigger_next_batch`.
            # This should also avoid concurrently sending in general since the set of documents
            # in both calls should overlap. (Since we always include all previously unsent documents.)
            try:
                self.env['res.company']._with_locked_records(documents)
            except UserError:
                # We will later make sure that we trigger the cron again
                continue

            # We sort the `documents` to batch them in the order they were chained
            documents = documents.sorted('chain_index')

            # Send batches with size BATCH_LIMIT; they are not restricted by the waiting time
            next_batch = documents[:BATCH_LIMIT]
            start_index = 0
            while len(next_batch) == BATCH_LIMIT:
                next_batch.with_company(company)._send_as_batch()
                start_index += BATCH_LIMIT
                next_batch = documents[start_index:start_index + BATCH_LIMIT]
            # Now: len(next_batch) < BATCH_LIMIT ; we need to respect the waiting time

            if not next_batch:
                continue

            next_batch_time = company.l10n_es_edi_verifactu_next_batch_time
            if not next_batch_time or fields.Datetime.now() >= next_batch_time:
                next_batch.with_company(company)._send_as_batch()
            else:
                # Since we have a `next_batch_time` the `next_trigger_time` will be set to a datetime
                # We set it to the minimum of all the already encountered `next_batch_time`
                next_trigger_time = min(next_trigger_time or datetime.max, next_batch_time)

        # In case any of the documents were not successfully sent we trigger the cron again in 60s
        # (or at the next batch time if the 60s is earlier)
        for company, documents in documents_per_company:
            unsent_documents = documents.filtered_domain(unsent_domain)
            next_batch_time = company.l10n_es_edi_verifactu_next_batch_time
            if unsent_documents:
                # Trigger in 60s or at the next batch time (except if there is an earlier trigger already)
                in_60_seconds = fields.Datetime.now() + timedelta(seconds=60)
                company_next_trigger_time = max(in_60_seconds, next_batch_time or datetime.min)
                # Set `next_trigger_time` to the minimum of all the already encountered trigger times
                next_trigger_time = min(next_trigger_time or datetime.max, company_next_trigger_time)

        if next_trigger_time:
            cron = self.env.ref('l10n_es_edi_verifactu.cron_verifactu_batch', raise_if_not_found=False)
            if cron:
                cron._trigger(at=next_trigger_time)