def thread_to_document(full_thread: dict[str, Any], email_used_to_fetch_thread: str) -> Document | None:
    """Convert Gmail thread to Document object."""
    all_messages = full_thread.get("messages", [])
    if not all_messages:
        return None

    sections = []
    semantic_identifier = ""
    updated_at = None
    from_emails: dict[str, str | None] = {}
    other_emails: dict[str, str | None] = {}

    for message in all_messages:
        section, message_metadata = message_to_section(message)
        sections.append(section)

        for name, value in message_metadata.items():
            if name in EMAIL_FIELDS:
                email, display_name = clean_email_and_extract_name(value)
                if name == "from":
                    from_emails[email] = display_name if not from_emails.get(email) else None
                else:
                    other_emails[email] = display_name if not other_emails.get(email) else None

        if not semantic_identifier:
            semantic_identifier = message_metadata.get("subject", "")
            semantic_identifier = clean_string(semantic_identifier)
            semantic_identifier = sanitize_filename(semantic_identifier)

        if message_metadata.get("updated_at"):
            updated_at = message_metadata.get("updated_at")

    updated_at_datetime = None
    if updated_at:
        updated_at_datetime = gmail_time_str_to_utc(updated_at)

    thread_id = full_thread.get("id")
    if not thread_id:
        raise ValueError("Thread ID is required")

    primary_owners = _get_owners_from_emails(from_emails)
    secondary_owners = _get_owners_from_emails(other_emails)

    if not semantic_identifier:
        semantic_identifier = "(no subject)"

    combined_sections = "\n\n".join(
        sec.text for sec in sections if hasattr(sec, "text")
    )
    blob = combined_sections
    size_bytes = len(blob)
    extension = '.txt'

    return Document(
        id=thread_id,
        semantic_identifier=semantic_identifier,
        blob=blob,
        size_bytes=size_bytes,
        extension=extension,
        source=DocumentSource.GMAIL,
        primary_owners=primary_owners,
        secondary_owners=secondary_owners,
        doc_updated_at=updated_at_datetime,
        metadata=message_metadata,
        external_access=ExternalAccess(
            external_user_emails={email_used_to_fetch_thread},
            external_user_group_ids=set(),
            is_public=False,
        ),
    )