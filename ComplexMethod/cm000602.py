async def _build_reply_message(
    service, input_data, execution_context: ExecutionContext
) -> tuple[str, str]:
    """
    Builds a reply MIME message for Gmail threads.

    Returns:
        tuple: (base64-encoded raw message, threadId)
    """
    # Get parent message for reply context
    parent = await asyncio.to_thread(
        lambda: service.users()
        .messages()
        .get(
            userId="me",
            id=input_data.parentMessageId,
            format="metadata",
            metadataHeaders=[
                "Subject",
                "References",
                "Message-ID",
                "From",
                "To",
                "Cc",
                "Reply-To",
            ],
        )
        .execute()
    )

    # Build headers dictionary, preserving all values for duplicate headers
    headers = {}
    for h in parent.get("payload", {}).get("headers", []):
        name = h["name"].lower()
        value = h["value"]
        if name in headers:
            # For duplicate headers, keep the first occurrence (most relevant for reply context)
            continue
        headers[name] = value

    # Determine recipients if not specified
    if not (input_data.to or input_data.cc or input_data.bcc):
        if input_data.replyAll:
            recipients = [parseaddr(headers.get("from", ""))[1]]
            recipients += [addr for _, addr in getaddresses([headers.get("to", "")])]
            recipients += [addr for _, addr in getaddresses([headers.get("cc", "")])]
            # Use dict.fromkeys() for O(n) deduplication while preserving order
            input_data.to = list(dict.fromkeys(filter(None, recipients)))
        else:
            # Check Reply-To header first, fall back to From header
            reply_to = headers.get("reply-to", "")
            from_addr = headers.get("from", "")
            sender = parseaddr(reply_to if reply_to else from_addr)[1]
            input_data.to = [sender] if sender else []

    # Set subject with Re: prefix if not already present
    if input_data.subject:
        subject = input_data.subject
    else:
        parent_subject = headers.get("subject", "").strip()
        # Only add "Re:" if not already present (case-insensitive check)
        if parent_subject.lower().startswith("re:"):
            subject = parent_subject
        else:
            subject = f"Re: {parent_subject}" if parent_subject else "Re:"

    # Build references header for proper threading
    references = headers.get("references", "").split()
    if headers.get("message-id"):
        references.append(headers["message-id"])

    # Create MIME message
    validate_all_recipients(input_data)

    msg = MIMEMultipart()
    if input_data.to:
        msg["To"] = serialize_email_recipients(input_data.to)
    if input_data.cc:
        msg["Cc"] = serialize_email_recipients(input_data.cc)
    if input_data.bcc:
        msg["Bcc"] = serialize_email_recipients(input_data.bcc)
    msg["Subject"] = subject
    if headers.get("message-id"):
        msg["In-Reply-To"] = headers["message-id"]
    if references:
        msg["References"] = " ".join(references)

    # Use the helper function for consistent content type handling
    msg.attach(_make_mime_text(input_data.body, input_data.content_type))

    # Handle attachments
    for attach in input_data.attachments:
        local_path = await store_media_file(
            file=attach,
            execution_context=execution_context,
            return_format="for_local_processing",
        )
        assert execution_context.graph_exec_id  # Validated by store_media_file
        abs_path = get_exec_file_path(execution_context.graph_exec_id, local_path)
        part = MIMEBase("application", "octet-stream")
        with open(abs_path, "rb") as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", f"attachment; filename={Path(abs_path).name}"
        )
        msg.attach(part)

    # Encode message
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return raw, input_data.threadId