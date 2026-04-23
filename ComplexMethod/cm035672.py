def create_events(event_data):
    events = []
    # Import necessary types here to avoid repeated imports inside the loop
    from openhands.events.action import CmdRunAction, RecallAction
    from openhands.events.observation import CmdOutputObservation, RecallObservation

    for i, data in enumerate(event_data):
        event_type = data['type']
        source = data.get('source', EventSource.AGENT)
        kwargs = {}  # Arguments for the event constructor

        # Determine arguments based on event type
        if event_type == RecallAction:
            kwargs['query'] = data.get('query', '')
            kwargs['recall_type'] = data.get('recall_type', RecallType.KNOWLEDGE)
        elif event_type == RecallObservation:
            kwargs['content'] = data.get('content', '')
            kwargs['recall_type'] = data.get('recall_type', RecallType.KNOWLEDGE)
        elif event_type == CmdRunAction:
            kwargs['command'] = data.get('command', '')
        elif event_type == CmdOutputObservation:
            # Required args for CmdOutputObservation
            kwargs['content'] = data.get('content', '')
            kwargs['command'] = data.get('command', '')
            # Pass command_id via kwargs if present in data
            if 'command_id' in data:
                kwargs['command_id'] = data['command_id']
            # Pass metadata if present
            if 'metadata' in data:
                kwargs['metadata'] = data['metadata']
        else:  # Default for MessageAction, SystemMessageAction, etc.
            kwargs['content'] = data.get('content', '')

        # Instantiate the event
        event = event_type(**kwargs)

        # Assign internal attributes AFTER instantiation
        event._id = i + 1  # Assign sequential IDs starting from 1
        event._source = source
        # Assign _cause using cause_id from data, AFTER event._id is set
        if 'cause_id' in data:
            event._cause = data['cause_id']
        # If command_id was NOT passed via kwargs but cause_id exists,
        # pass cause_id as command_id to __init__ via kwargs for legacy handling
        # This needs to happen *before* instantiation if we want __init__ to handle it
        # Let's adjust the logic slightly:
        if event_type == CmdOutputObservation:
            if 'command_id' not in kwargs and 'cause_id' in data:
                kwargs['command_id'] = data['cause_id']  # Let __init__ handle this
            # Re-instantiate if we added command_id
            if 'command_id' in kwargs and event.command_id != kwargs['command_id']:
                event = event_type(**kwargs)
                event._id = i + 1
                event._source = source

        # Now assign _cause if it exists in data, after potential re-instantiation
        if 'cause_id' in data:
            event._cause = data['cause_id']

        events.append(event)
    return events