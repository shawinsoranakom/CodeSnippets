def _assert_batch(
        self,
        batch: list,
        *,
        require_fifo_queue_params: bool = False,
        require_message_deduplication_id: bool = False,
        max_messages_override: int | None = None,
    ) -> None:
        if not batch:
            raise EmptyBatchRequest

        max_messages_per_batch = max_messages_override or MAX_NUMBER_OF_MESSAGES
        if batch and (no_entries := len(batch)) > max_messages_per_batch:
            raise TooManyEntriesInBatchRequest(
                f"Maximum number of entries per request are {max_messages_per_batch}. You have sent {no_entries}."
            )
        visited = set()
        for entry in batch:
            entry_id = entry["Id"]
            if not re.search(r"^[\w-]+$", entry_id) or len(entry_id) > 80:
                raise InvalidBatchEntryId(
                    "A batch entry id can only contain alphanumeric characters, hyphens and underscores. "
                    "It can be at most 80 letters long."
                )
            if require_message_deduplication_id and not entry.get("MessageDeduplicationId"):
                raise InvalidParameterValueException(
                    "The queue should either have ContentBasedDeduplication enabled or "
                    "MessageDeduplicationId provided explicitly"
                )
            if require_fifo_queue_params and not entry.get("MessageGroupId"):
                raise InvalidParameterValueException(
                    "The request must contain the parameter MessageGroupId."
                )
            if entry_id in visited:
                raise BatchEntryIdsNotDistinct()
            else:
                visited.add(entry_id)