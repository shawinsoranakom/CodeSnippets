def event_from_dict(data: dict[str, Any]) -> 'Event':
    evt: Event
    if 'action' in data:
        evt = action_from_dict(data)
    elif 'observation' in data:
        evt = observation_from_dict(data)
    else:
        raise ValueError(f'Unknown event type: {data}')
    for key in UNDERSCORE_KEYS:
        if key in data:
            value = data[key]
            if key == 'timestamp' and isinstance(value, datetime):
                value = value.isoformat()
            if key == 'source':
                value = EventSource(value)
            if key == 'tool_call_metadata':
                value = ToolCallMetadata(**value)
            if key == 'llm_metrics':
                metrics = Metrics()
                if isinstance(value, dict):
                    metrics.accumulated_cost = value.get('accumulated_cost', 0.0)
                    # Set max_budget_per_task if available
                    metrics.max_budget_per_task = value.get('max_budget_per_task')
                    for cost in value.get('costs', []):
                        metrics._costs.append(Cost(**cost))
                    metrics.response_latencies = [
                        ResponseLatency(**latency)
                        for latency in value.get('response_latencies', [])
                    ]
                    metrics.token_usages = [
                        TokenUsage(**usage) for usage in value.get('token_usages', [])
                    ]
                    # Set accumulated token usage if available
                    if 'accumulated_token_usage' in value:
                        metrics._accumulated_token_usage = TokenUsage(
                            **value.get('accumulated_token_usage', {})
                        )
                value = metrics
            setattr(evt, '_' + key, value)
    return evt