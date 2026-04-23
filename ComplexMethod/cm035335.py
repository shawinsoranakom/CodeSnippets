def event_to_dict(event: 'Event') -> dict:
    props = asdict(event)
    d = {}
    for key in TOP_KEYS:
        if hasattr(event, key) and getattr(event, key) is not None:
            d[key] = getattr(event, key)
        elif hasattr(event, f'_{key}') and getattr(event, f'_{key}') is not None:
            d[key] = getattr(event, f'_{key}')
        if key == 'id' and d.get('id') == -1:
            d.pop('id', None)
        if key == 'timestamp' and 'timestamp' in d:
            if isinstance(d['timestamp'], datetime):
                d['timestamp'] = d['timestamp'].isoformat()
        if key == 'source' and 'source' in d:
            d['source'] = d['source'].value
        if key == 'recall_type' and 'recall_type' in d:
            d['recall_type'] = d['recall_type'].value
        if key == 'tool_call_metadata' and 'tool_call_metadata' in d:
            d['tool_call_metadata'] = d['tool_call_metadata'].model_dump()
        if key == 'llm_metrics' and 'llm_metrics' in d:
            d['llm_metrics'] = d['llm_metrics'].get()
        props.pop(key, None)

    if 'security_risk' in props and props['security_risk'] is None:
        props.pop('security_risk')

    # Remove task_completed from serialization when it's None (backward compatibility)
    if 'task_completed' in props and props['task_completed'] is None:
        props.pop('task_completed')
    if 'action' in d:
        # Handle security_risk for actions - include it in args
        if 'security_risk' in props:
            props['security_risk'] = props['security_risk'].value
        d['args'] = props
        if event.timeout is not None:
            d['timeout'] = event.timeout
    elif 'observation' in d:
        d['content'] = props.pop('content', '')

        # props is a dict whose values can include a complex object like an instance of a BaseModel subclass
        # such as CmdOutputMetadata
        # we serialize it along with the rest
        # we also handle the Enum conversion for RecallObservation
        d['extras'] = {
            k: (v.value if isinstance(v, Enum) else _convert_pydantic_to_dict(v))
            for k, v in props.items()
        }
        # Include success field for CmdOutputObservation
        if hasattr(event, 'success'):
            d['success'] = event.success
    else:
        raise ValueError(f'Event must be either action or observation. has: {event}')
    return d