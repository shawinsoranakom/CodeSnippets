async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        conversation: JsonConversation = None,
        **kwargs
    ) -> AsyncResult:
        is_new_conversation = conversation is None or not hasattr(conversation, 'session_hash')
        if is_new_conversation:
            conversation = JsonConversation(session_hash=str(uuid.uuid4()).replace('-', '')[:12])

        model = cls.get_model(model)
        prompt = format_prompt(messages) if is_new_conversation else get_last_user_message(messages)

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': cls.url,
            'referer': f'{cls.url}/',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
        }

        payload = {
            "data": [
                prompt,
                [
                    [
                        None,
                        "Hello! I'm Ling. Try selecting a scenario and a message example below to get started."
                    ]
                ],
                get_system_prompt(messages),
                1,
                model
            ],
            "event_data": None,
            "fn_index": 11,
            "trigger_id": 33,
            "session_hash": conversation.session_hash
        }
        payload = {
    "data": [
        "4aa9d0c6-81c2-4274-91c5-a0d96d827916",
        [
            {
                "id": "4aa9d0c6-81c2-4274-91c5-a0d96d827917",
                "title": "(New Conversation)",
                "messages": [],
                "timestamp": "2026-02-11T23:28:14.398499",
                "system_prompt": "",
                "model": "🦉 Ling-1T",
                "temperature": 0.7
            }
        ],
        "🦉 Ling-1T",
        "hi",
        [],
        "",
        0.7
    ],
    "fn_index": 11,
    "trigger_id": 33,
    "session_hash": "bis3t7jioto"
}

        async with aiohttp.ClientSession() as session:
            async with session.post(cls.api_endpoint, headers=headers, json=payload, proxy=proxy) as response:
                await raise_for_status(response)
                # Response body must be consumed for the request to complete
                await response.json()

            data_url = f'{cls.url}/gradio_api/queue/data?session_hash={conversation.session_hash}'
            headers_data = {
                'accept': 'text/event-stream',
                'referer': f'{cls.url}/',
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
            }

            async with session.get(data_url, headers=headers_data, proxy=proxy) as response:
                full_response = ""
                async for line in response.content:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        try:
                            json_data = json.loads(decoded_line[6:])
                            if json_data.get('msg') == 'process_generating':
                                if 'output' in json_data and 'data' in json_data['output']:
                                    output_data = json_data['output']['data']
                                    if output_data and len(output_data) > 0:
                                        parts = output_data[0][0]
                                        if len(parts) == 2:
                                            new_text = output_data[0][1].pop()
                                            full_response += new_text
                                            yield new_text
                                        if len(parts) > 2:
                                            new_text = parts[2]
                                            full_response += new_text
                                            yield new_text

                            elif json_data.get('msg') == 'process_completed':
                               break

                        except json.JSONDecodeError:
                            debug.log("Could not parse JSON:", decoded_line)