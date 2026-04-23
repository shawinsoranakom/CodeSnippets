def format_event_verbose_message(event: _messages.Event) -> str:
    """
    Format an event into a verbose message.
    Help text, contextual information and sub-events will be included.
    """
    segments: list[str] = []
    original_event = event

    while event:
        messages = [event.msg]
        chain: _messages.EventChain = event.chain

        while chain and chain.follow:
            if chain.event.events:
                break  # do not collapse a chained event with sub-events, since they would be lost

            if chain.event.formatted_source_context or chain.event.help_text:
                if chain.event.formatted_source_context != event.formatted_source_context or chain.event.help_text != event.help_text:
                    break  # do not collapse a chained event with different details, since they would be lost

            if chain.event.chain and chain.msg_reason != chain.event.chain.msg_reason:
                break  # do not collapse a chained event which has a chain with a different msg_reason

            messages.append(chain.event.msg)

            chain = chain.event.chain

        msg = _event_utils.deduplicate_message_parts(messages)
        segment = '\n'.join(_get_message_lines(msg, event.help_text, event.formatted_source_context)) + '\n'

        if event.events:
            child_msgs = [format_event_verbose_message(child) for child in event.events]
            segment += _format_event_children("Sub-Event", child_msgs)

        segments.append(segment)

        if chain and chain.follow:
            segments.append(f'\n{chain.msg_reason}\n\n')

            event = chain.event
        else:
            event = None

    if len(segments) > 1:
        segments.insert(0, _event_utils.format_event_brief_message(original_event) + '\n\n')

    return ''.join(segments)