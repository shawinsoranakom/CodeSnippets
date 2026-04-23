async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str | None = None,
        **kwargs
    ) -> AsyncResult:
        """
        Make an asynchronous request to the Chatai stream API.

        Args:
            model (str): The model name (currently ignored by this provider).
            messages (Messages): List of message dictionaries.
            proxy (str | None): Optional proxy URL.
            **kwargs: Additional arguments (currently unused).

        Yields:
            str: Chunks of the response text.

        Raises:
            Exception: If the API request fails.
        """

        # selected_model = cls.get_model(model) # Not sent in payload

        headers = {
            'Accept': 'text/event-stream',
            'Content-Type': 'application/json', 
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G935F Build/N2G48H)',
            'Host': 'chatai.aritek.app', 
            'Connection': 'Keep-Alive', 
        }

        static_machine_id = generate_machine_id()#"0343578260151264.464241743263788731"
        c_token = "eyJzdWIiOiIyMzQyZmczNHJ0MzR0MzQiLCJuYW1lIjoiSm9objM0NTM0NT"# might change 

        payload = {
            "machineId": static_machine_id,
            "msg": messages, # Pass the message list directly
            "token": c_token,
            "type": 0 
        }

        async with ClientSession(headers=headers) as session:
            try:
                async with session.post(
                    cls.api_endpoint,
                    json=payload,
                    proxy=proxy
                ) as response:
                    response.raise_for_status() # Check for HTTP errors (4xx, 5xx)

                    # Process the Server-Sent Events (SSE) stream
                    async for line_bytes in response.content:
                        if not line_bytes:
                            continue # Skip empty linesw

                        line = line_bytes.decode('utf-8').strip()

                        if line.startswith("data:"):
                            data_str = line[len("data:"):].strip()

                            if data_str == "[DONE]":
                                break # End of stream signal

                            try:
                                chunk_data = json.loads(data_str)
                                choices = chunk_data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content_chunk = delta.get("content")
                                    if content_chunk:
                                        yield content_chunk
                                    # Check for finish reason if needed (e.g., to stop early)
                                    # finish_reason = choices[0].get("finish_reason")
                                    # if finish_reason:
                                    #     break
                            except json.JSONDecodeError:
                                debug.error(f"Warning: Could not decode JSON: {data_str}")
                                continue
                            except Exception as e:
                                debug.error(f"Warning: Error processing chunk: {e}")
                                continue

            except Exception as e:
                # print()
                debug.error(f"Error during Chatai API request: {e}")
                raise e