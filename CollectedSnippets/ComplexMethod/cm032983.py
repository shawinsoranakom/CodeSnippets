def _convert_message_to_document(
    message: DiscordMessage,
    sections: list[TextSection],
) -> Document:
    """
    Convert a discord message to a document
    Sections are collected before calling this function because it relies on async
        calls to fetch the thread history if there is one
    """

    metadata: dict[str, str | list[str]] = {}
    semantic_substring = ""

    # Only messages from TextChannels will make it here, but we have to check for it anyway
    if isinstance(message.channel, TextChannel) and (channel_name := message.channel.name):
        metadata["Channel"] = channel_name
        semantic_substring += f" in Channel: #{channel_name}"

    # If there is a thread, add more detail to the metadata, title, and semantic identifier
    if isinstance(message.channel, Thread):
        # Threads do have a title
        title = message.channel.name

        # Add more detail to the semantic identifier if available
        semantic_substring += f" in Thread: {title}"

    snippet: str = message.content[:_SNIPPET_LENGTH].rstrip() + "..." if len(message.content) > _SNIPPET_LENGTH else message.content

    semantic_identifier = f"{message.author.name} said{semantic_substring}: {snippet}"

    # fallback to created_at
    doc_updated_at = message.edited_at if message.edited_at else message.created_at
    if doc_updated_at and doc_updated_at.tzinfo is None:
        doc_updated_at = doc_updated_at.replace(tzinfo=timezone.utc)
    elif doc_updated_at:
        doc_updated_at = doc_updated_at.astimezone(timezone.utc)

    return Document(
        id=f"{_DISCORD_DOC_ID_PREFIX}{message.id}",
        source=DocumentSource.DISCORD,
        semantic_identifier=semantic_identifier,
        doc_updated_at=doc_updated_at,
        blob=message.content.encode("utf-8"),
        extension=".txt",
        size_bytes=len(message.content.encode("utf-8")),
        metadata=metadata if metadata else None,
    )