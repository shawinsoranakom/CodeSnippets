def _fetch_threads(
        self,
        time_range_start: SecondsSinceUnixEpoch | None = None,
        time_range_end: SecondsSinceUnixEpoch | None = None,
    ) -> GenerateDocumentsOutput:
        """Fetch Gmail threads within time range."""
        query = build_time_range_query(time_range_start, time_range_end)
        doc_batch = []

        for user_email in self._get_all_user_emails():
            gmail_service = get_gmail_service(self.creds, user_email)
            try:
                for thread in execute_paginated_retrieval(
                    retrieval_function=gmail_service.users().threads().list,
                    list_key="threads",
                    userId=user_email,
                    fields=THREAD_LIST_FIELDS,
                    q=query,
                    continue_on_404_or_403=True,
                ):
                    full_thread = _execute_single_retrieval(
                        retrieval_function=gmail_service.users().threads().get,
                        userId=user_email,
                        fields=THREAD_FIELDS,
                        id=thread["id"],
                        continue_on_404_or_403=True,
                    )
                    doc = thread_to_document(full_thread, user_email)
                    if doc is None:
                        continue

                    doc_batch.append(doc)
                    if len(doc_batch) > self.batch_size:
                        yield doc_batch
                        doc_batch = []
            except HttpError as e:
                if is_mail_service_disabled_error(e):
                    logging.warning(
                        "Skipping Gmail sync for %s because the mailbox is disabled.",
                        user_email,
                    )
                    continue
                raise

        if doc_batch:
            yield doc_batch