async def run(
        self, input_data: Input, *, credentials: RedditCredentials, **kwargs
    ) -> BlockOutput:
        try:
            raw_items = self.get_inbox(
                credentials, input_data.inbox_type, input_data.limit
            )
            all_items = []

            for item in raw_items:
                # Determine item type
                if hasattr(item, "was_comment") and item.was_comment:
                    if hasattr(item, "subject") and "mention" in item.subject.lower():
                        item_type = "mention"
                    else:
                        item_type = "comment_reply"
                else:
                    item_type = "message"

                inbox_item = RedditInboxItem(
                    item_id=item.id,
                    item_type=item_type,
                    subject=item.subject if hasattr(item, "subject") else "",
                    body=item.body,
                    author=str(item.author) if item.author else "[deleted]",
                    created_utc=item.created_utc,
                    is_read=not item.new,
                    context=item.context if hasattr(item, "context") else None,
                )
                all_items.append(inbox_item)
                yield "item", inbox_item

            # Mark as read if requested
            if input_data.mark_read and raw_items:
                client = get_praw(credentials)
                client.inbox.mark_read(raw_items)

            yield "items", all_items
        except Exception as e:
            yield "error", str(e)