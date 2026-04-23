def convert_fncall_messages_to_non_fncall_messages(
    messages: list[dict],
    tools: list[ChatCompletionToolParam],
    add_in_context_learning_example: bool = True,
) -> list[dict]:
    """Convert function calling messages to non-function calling messages."""
    messages = copy.deepcopy(messages)

    formatted_tools = convert_tools_to_description(tools)
    system_prompt_suffix = SYSTEM_PROMPT_SUFFIX_TEMPLATE.format(
        description=formatted_tools
    )

    converted_messages = []
    first_user_message_encountered = False
    for message in messages:
        role = message['role']
        content = message['content']

        # 1. SYSTEM MESSAGES
        # append system prompt suffix to content
        if role == 'system':
            if isinstance(content, str):
                content += system_prompt_suffix
            elif isinstance(content, list):
                if content and content[-1]['type'] == 'text':
                    content[-1]['text'] += system_prompt_suffix
                else:
                    content.append({'type': 'text', 'text': system_prompt_suffix})
            else:
                raise FunctionCallConversionError(
                    f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                )
            converted_messages.append({'role': 'system', 'content': content})

        # 2. USER MESSAGES (no change)
        elif role == 'user':
            # Add in-context learning example for the first user message
            if not first_user_message_encountered and add_in_context_learning_example:
                first_user_message_encountered = True

                # Generate example based on available tools
                example = IN_CONTEXT_LEARNING_EXAMPLE_PREFIX(tools)

                # Add example if we have any tools
                if example:
                    # add in-context learning example
                    if isinstance(content, str):
                        content = example + content + IN_CONTEXT_LEARNING_EXAMPLE_SUFFIX
                    elif isinstance(content, list):
                        if content and content[0]['type'] == 'text':
                            content[0]['text'] = (
                                example
                                + content[0]['text']
                                + IN_CONTEXT_LEARNING_EXAMPLE_SUFFIX
                            )
                        else:
                            content = (
                                [
                                    {
                                        'type': 'text',
                                        'text': example,
                                    }
                                ]
                                + content
                                + [
                                    {
                                        'type': 'text',
                                        'text': IN_CONTEXT_LEARNING_EXAMPLE_SUFFIX,
                                    }
                                ]
                            )
                    else:
                        raise FunctionCallConversionError(
                            f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                        )
            converted_messages.append(
                {
                    'role': 'user',
                    'content': content,
                }
            )

        # 3. ASSISTANT MESSAGES
        # - 3.1 no change if no function call
        # - 3.2 change if function call
        elif role == 'assistant':
            if 'tool_calls' in message and message['tool_calls'] is not None:
                if len(message['tool_calls']) != 1:
                    raise FunctionCallConversionError(
                        f'Expected exactly one tool call in the message. More than one tool call is not supported. But got {len(message["tool_calls"])} tool calls. Content: {content}'
                    )
                try:
                    tool_content = convert_tool_call_to_string(message['tool_calls'][0])
                except FunctionCallConversionError as e:
                    raise FunctionCallConversionError(
                        f'Failed to convert tool call to string.\nCurrent tool call: {message["tool_calls"][0]}.\nRaw messages: {json.dumps(messages, indent=2)}'
                    ) from e
                if isinstance(content, str):
                    content += '\n\n' + tool_content
                    content = content.lstrip()
                elif isinstance(content, list):
                    if content and content[-1]['type'] == 'text':
                        content[-1]['text'] += '\n\n' + tool_content
                        content[-1]['text'] = content[-1]['text'].lstrip()
                    else:
                        content.append({'type': 'text', 'text': tool_content})
                else:
                    raise FunctionCallConversionError(
                        f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                    )
            converted_messages.append({'role': 'assistant', 'content': content})

        # 4. TOOL MESSAGES (tool outputs)
        elif role == 'tool':
            # Convert tool result as user message
            tool_name = message.get('name', 'function')
            prefix = f'EXECUTION RESULT of [{tool_name}]:\n'
            # and omit "tool_call_id" AND "name"
            if isinstance(content, str):
                content = prefix + content
            elif isinstance(content, list):
                if content and (
                    first_text_content := next(
                        (c for c in content if c['type'] == 'text'), None
                    )
                ):
                    first_text_content['text'] = prefix + first_text_content['text']
                else:
                    content = [{'type': 'text', 'text': prefix}] + content
            else:
                raise FunctionCallConversionError(
                    f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                )
            if 'cache_control' in message:
                content[-1]['cache_control'] = {'type': 'ephemeral'}
            converted_messages.append({'role': 'user', 'content': content})
        else:
            raise FunctionCallConversionError(
                f'Unexpected role {role}. Expected system, user, assistant or tool.'
            )
    return converted_messages