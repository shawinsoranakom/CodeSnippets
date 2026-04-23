async def _fetch_documents_from_channel(
    channel: TextChannel,
    start_time: datetime | None,
    end_time: datetime | None,
) -> AsyncIterable[Document]:
    # Discord's epoch starts at 2015-01-01
    discord_epoch = datetime(2015, 1, 1, tzinfo=timezone.utc)
    if start_time and start_time < discord_epoch:
        start_time = discord_epoch

    # NOTE: limit=None is the correct way to fetch all messages and threads with pagination
    # The discord package erroneously uses limit for both pagination AND number of results
    # This causes the history and archived_threads methods to return 100 results even if there are more results within the filters
    # Pagination is handled automatically (100 results at a time) when limit=None

    async for channel_message in channel.history(
        limit=None,
        after=start_time,
        before=end_time,
    ):
        # Skip messages that are not the default type
        if channel_message.type != MessageType.default:
            continue

        sections: list[TextSection] = [
            TextSection(
                text=channel_message.content,
                link=channel_message.jump_url,
            )
        ]

        yield _convert_message_to_document(channel_message, sections)

    for active_thread in channel.threads:
        async for thread_message in active_thread.history(
            limit=None,
            after=start_time,
            before=end_time,
        ):
            # Skip messages that are not the default type
            if thread_message.type != MessageType.default:
                continue

            sections = [
                TextSection(
                    text=thread_message.content,
                    link=thread_message.jump_url,
                )
            ]

            yield _convert_message_to_document(thread_message, sections)

    async for archived_thread in channel.archived_threads(
        limit=None,
    ):
        async for thread_message in archived_thread.history(
            limit=None,
            after=start_time,
            before=end_time,
        ):
            # Skip messages that are not the default type
            if thread_message.type != MessageType.default:
                continue

            sections = [
                TextSection(
                    text=thread_message.content,
                    link=thread_message.jump_url,
                )
            ]

            yield _convert_message_to_document(thread_message, sections)