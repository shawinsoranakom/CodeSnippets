def _ticket_to_document(
    ticket: dict[str, Any],
    author_map: dict[str, BasicExpertInfo],
    client: ZendeskClient,
) -> tuple[dict[str, BasicExpertInfo] | None, Document]:
    submitter_id = ticket.get("submitter")
    if not submitter_id:
        submitter = None
    else:
        submitter = (
            author_map.get(submitter_id)
            if submitter_id in author_map
            else _fetch_author(client, submitter_id)
        )

    new_author_mapping = (
        {submitter_id: submitter} if submitter_id and submitter else None
    )

    updated_at = ticket.get("updated_at")
    update_time = time_str_to_utc(updated_at) if updated_at else None

    metadata: dict[str, str | list[str]] = {}
    if status := ticket.get("status"):
        metadata["status"] = status
    if priority := ticket.get("priority"):
        metadata["priority"] = priority
    if tags := ticket.get("tags"):
        metadata["tags"] = tags
    if ticket_type := ticket.get("type"):
        metadata["ticket_type"] = ticket_type

    # Fetch comments for the ticket
    comments_data = client.make_request(f"tickets/{ticket.get('id')}/comments", {})
    comments = comments_data.get("comments", [])

    comment_texts = []
    for comment in comments:
        new_author_mapping, comment_text = _get_comment_text(
            comment, author_map, client
        )
        if new_author_mapping:
            author_map.update(new_author_mapping)
        comment_texts.append(comment_text)

    comments_text = "\n\n".join(comment_texts)

    subject = ticket.get("subject")
    full_text = f"Ticket Subject:\n{subject}\n\nComments:\n{comments_text}"

    blob = full_text.encode("utf-8", errors="replace")
    return new_author_mapping, Document(
        id=f"zendesk_ticket_{ticket['id']}",
        blob=blob,
        extension=".txt",
        size_bytes=len(blob),
        source=DocumentSource.ZENDESK,
        semantic_identifier=f"Ticket #{ticket['id']}: {subject or 'No Subject'}",
        doc_updated_at=update_time,
        primary_owners=[submitter] if submitter else None,
        metadata=metadata,
    )