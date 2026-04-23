async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        **kwargs
    ) -> AsyncResult:
        model = cls.get_model(model)

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://mintlify.com",
            "priority": "u=1, i",
            "referer": "https://mintlify.com/",
            "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }

        async with ClientSession(headers=headers) as session:
            # Format the system prompt with current date/time
            current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            formatted_system_prompt = cls.system_prompt.format(currentDateTime=current_datetime)

            # Convert messages to the expected format
            formatted_messages = []

            # Add system message first
            system_msg_id = f"sys_{datetime.now().timestamp()}".replace(".", "")[:16]
            formatted_messages.append({
                "id": system_msg_id,
                "createdAt": datetime.now().isoformat() + "Z",
                "role": "system",
                "content": formatted_system_prompt,
                "parts": [{"type": "text", "text": formatted_system_prompt}]
            })

            # Add user messages
            for msg in messages:
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                else:
                    role = getattr(msg, "role", "user")
                    content = getattr(msg, "content", "")

                # Skip if it's a system message (we already added our own)
                if role == "system":
                    continue

                # Generate a simple ID for the message
                msg_id = f"msg_{datetime.now().timestamp()}".replace(".", "")[:16]

                formatted_messages.append({
                    "id": msg_id,
                    "createdAt": datetime.now().isoformat() + "Z",
                    "role": role,
                    "content": content,
                    "parts": [{"type": "text", "text": content}]
                })

            data = {
                "id": "mintlify",
                "messages": formatted_messages,
                "fp": "mintlify"
            }

            async with session.post(cls.api_endpoint, json=data, proxy=proxy) as response:
                response.raise_for_status()

                buffer = ""
                async for chunk in response.content:
                    if chunk:
                        buffer += chunk.decode('utf-8', errors='ignore')
                        lines = buffer.split('\n')
                        buffer = lines[-1]  # Keep incomplete line in buffer

                        for line in lines[:-1]:
                            if line.startswith('0:'):
                                # Extract the text content from streaming chunks
                                text = line[2:]
                                if text.startswith('"') and text.endswith('"'):
                                    text = json.loads(text)
                                yield text
                            elif line.startswith('f:'):
                                # Initial message ID response - skip
                                continue
                            elif line.startswith('e:') or line.startswith('d:'):
                                # End of stream with metadata - skip
                                continue