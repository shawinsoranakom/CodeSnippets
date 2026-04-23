def _load_from_checkpoint(
        self,
        start: SecondsSinceUnixEpoch,
        end: SecondsSinceUnixEpoch,
        checkpoint: ImapCheckpoint,
        include_perm_sync: bool,
    ) -> CheckpointOutput[ImapCheckpoint]:
        checkpoint = cast(ImapCheckpoint, copy.deepcopy(checkpoint))
        checkpoint.has_more = True

        mail_client = self._get_mail_client()

        if checkpoint.todo_mailboxes is None:
            # This is the dummy checkpoint.
            # Fill it with mailboxes first.
            if self._mailboxes:
                checkpoint.todo_mailboxes = _sanitize_mailbox_names(self._mailboxes)
            else:
                fetched_mailboxes = _fetch_all_mailboxes_for_email_account(
                    mail_client=mail_client
                )
                if not fetched_mailboxes:
                    raise RuntimeError(
                        "Failed to find any mailboxes for this email account"
                    )
                checkpoint.todo_mailboxes = _sanitize_mailbox_names(fetched_mailboxes)

            return checkpoint

        if (
            not checkpoint.current_mailbox
            or not checkpoint.current_mailbox.todo_email_ids
        ):
            if not checkpoint.todo_mailboxes:
                checkpoint.has_more = False
                return checkpoint

            mailbox = checkpoint.todo_mailboxes.pop()
            email_ids = _fetch_email_ids_in_mailbox(
                mail_client=mail_client,
                mailbox=mailbox,
                start=start,
                end=end,
            )
            checkpoint.current_mailbox = CurrentMailbox(
                mailbox=mailbox,
                todo_email_ids=email_ids,
            )

        _select_mailbox(
            mail_client=mail_client, mailbox=checkpoint.current_mailbox.mailbox
        )
        current_todos = cast(
            list, copy.deepcopy(checkpoint.current_mailbox.todo_email_ids[:_PAGE_SIZE])
        )
        checkpoint.current_mailbox.todo_email_ids = (
            checkpoint.current_mailbox.todo_email_ids[_PAGE_SIZE:]
        )

        for email_id in current_todos:
            email_msg = _fetch_email(mail_client=mail_client, email_id=email_id)
            if not email_msg:
                logging.warning(f"Failed to fetch message {email_id=}; skipping")
                continue

            email_headers = EmailHeaders.from_email_msg(email_msg=email_msg)
            msg_dt = email_headers.date
            if msg_dt.tzinfo is None:
                msg_dt = msg_dt.replace(tzinfo=timezone.utc)
            else:
                msg_dt = msg_dt.astimezone(timezone.utc)

            start_dt = datetime.fromtimestamp(start, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(end, tz=timezone.utc)

            if not (start_dt < msg_dt <= end_dt):
                continue

            email_doc = _convert_email_headers_and_body_into_document(
                email_msg=email_msg,
                email_headers=email_headers,
                include_perm_sync=include_perm_sync,
            )
            yield email_doc
            attachments = extract_attachments(email_msg)
            for att in attachments:
                yield attachment_to_document(email_doc, att, email_headers)

        return checkpoint