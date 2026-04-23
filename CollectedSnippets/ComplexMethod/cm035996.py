def is_mr_comment(message: Message, inline=False) -> bool:
        payload = message.message['payload']
        object_kind = payload.get('object_kind')
        event_type = payload.get('event_type')
        merge_request = payload.get('merge_request')

        if not (object_kind == 'note' and event_type in NOTE_TYPES and merge_request):
            return False

        # Check whether not belongs to MR
        object_attributes = payload.get('object_attributes', {})
        noteable_type = object_attributes.get('noteable_type')

        if noteable_type != 'MergeRequest':
            return False

        # Check whether comment is inline
        change_position = object_attributes.get('change_position')
        if inline and not change_position:
            return False
        if not inline and change_position:
            return False

        # Check body
        comment_body = object_attributes.get('note', '')
        return has_exact_mention(comment_body, INLINE_OH_LABEL)