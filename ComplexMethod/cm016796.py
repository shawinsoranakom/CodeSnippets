def normalize_history_item(prompt_id: str, history_item: dict, include_outputs: bool = False) -> dict:
    """Convert history item dict to unified job dict.

    History items have sensitive data already removed (prompt tuple has 5 elements).
    """
    prompt_tuple = history_item['prompt']
    priority, _, prompt, extra_data, _ = prompt_tuple
    create_time, workflow_id = _extract_job_metadata(extra_data)

    status_info = history_item.get('status', {})
    status_str = status_info.get('status_str') if status_info else None

    outputs = history_item.get('outputs', {})
    outputs_count, preview_output = get_outputs_summary(outputs)

    execution_error = None
    execution_start_time = None
    execution_end_time = None
    was_interrupted = False
    if status_info:
        messages = status_info.get('messages', [])
        for entry in messages:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                event_name, event_data = entry[0], entry[1]
                if isinstance(event_data, dict):
                    if event_name == 'execution_start':
                        execution_start_time = event_data.get('timestamp')
                    elif event_name in ('execution_success', 'execution_error', 'execution_interrupted'):
                        execution_end_time = event_data.get('timestamp')
                        if event_name == 'execution_error':
                            execution_error = event_data
                        elif event_name == 'execution_interrupted':
                            was_interrupted = True

    if status_str == 'success':
        status = JobStatus.COMPLETED
    elif status_str == 'error':
        status = JobStatus.CANCELLED if was_interrupted else JobStatus.FAILED
    else:
        status = JobStatus.COMPLETED

    job = prune_dict({
        'id': prompt_id,
        'status': status,
        'priority': priority,
        'create_time': create_time,
        'execution_start_time': execution_start_time,
        'execution_end_time': execution_end_time,
        'execution_error': execution_error,
        'outputs_count': outputs_count,
        'preview_output': preview_output,
        'workflow_id': workflow_id,
    })

    if include_outputs:
        job['outputs'] = normalize_outputs(outputs)
        job['execution_status'] = status_info
        job['workflow'] = {
            'prompt': prompt,
            'extra_data': extra_data,
        }

    return job