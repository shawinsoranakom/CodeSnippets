def test_malformed_parameter_parsing_recovery():
    """Ensure we can recover when models emit malformed parameter tags like <parameter=command=str_replace</parameter>.

    This simulates a tool call to str_replace_editor where the 'command' parameter is malformed.
    """
    from openhands.llm.fn_call_converter import (
        convert_non_fncall_messages_to_fncall_messages,
    )

    # Construct an assistant message with malformed parameter tag for 'command'
    assistant_message = {
        'role': 'assistant',
        'content': (
            '<function=str_replace_editor>\n'
            '<parameter=command=str_replace</parameter>\n'  # malformed form
            '<parameter=path>/repo/app.py</parameter>\n'
            '<parameter=old_str>foo</parameter>\n'
            '<parameter=new_str>bar</parameter>\n'
            '</function>'
        ),
    }

    messages = [
        {'role': 'system', 'content': 'test'},
        {'role': 'user', 'content': 'do edit'},
        assistant_message,
    ]

    converted = convert_non_fncall_messages_to_fncall_messages(messages, FNCALL_TOOLS)

    # The last message should be assistant with a parsed tool call
    last = converted[-1]
    assert last['role'] == 'assistant'
    assert 'tool_calls' in last and len(last['tool_calls']) == 1
    tool_call = last['tool_calls'][0]
    assert tool_call['type'] == 'function'
    assert tool_call['function']['name'] == 'str_replace_editor'

    # Arguments must be a valid JSON with command=str_replace and proper params
    args = json.loads(tool_call['function']['arguments'])
    assert args['command'] == 'str_replace'
    assert args['path'] == '/repo/app.py'
    assert args['old_str'] == 'foo'
    assert args['new_str'] == 'bar'