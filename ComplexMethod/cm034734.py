def _messages_to_gemini_format(messages: list, media: MediaListType) -> Dict[str, Any]:
        format_messages = []
        for msg in messages:
            # Convert a ChatMessage dict to GeminiFormattedMessage dict
            role = "model" if msg["role"] == "assistant" else "user"

            # Handle tool role (OpenAI style)
            # Group consecutive tool responses into a single user turn so that
            # the number of functionResponse parts equals the number of functionCall parts.
            if msg["role"] == "tool":
                tool_result = msg.get("content", "")
                func_response_part = {
                    "functionResponse": {
                        "name": msg.get("tool_call_id", "unknown_function"),
                        "response": {
                            "result": (
                                tool_result
                                if isinstance(tool_result, str)
                                else json.dumps(tool_result)
                            )
                        },
                    }
                }
                if (format_messages and format_messages[-1]["role"] == "user"
                        and any("functionResponse" in p for p in format_messages[-1]["parts"])):
                    format_messages[-1]["parts"].append(func_response_part)
                else:
                    format_messages.append({"role": "user", "parts": [func_response_part]})
                continue

            # Handle assistant messages with tool calls
            elif msg["role"] == "assistant" and msg.get("tool_calls"):
                parts = []
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    parts.append({"text": content})
                for tool_call in msg["tool_calls"]:
                    if tool_call.get("type") == "function":
                        func_call = {
                            "name": tool_call["function"]["name"],
                            "args": json.loads(tool_call["function"]["arguments"]),
                        }
                        # Restore thought_signature for Gemini thinking models when available
                        thought_sig = tool_call.get("extra_content", {}).get("google", {}).get("thought_signature", "skip_thought_signature_validator")
                        parts.append({"functionCall": func_call, "thoughtSignature": thought_sig})

            # Handle string content
            elif isinstance(msg["content"], str):
                parts = [{"text": msg["content"]}]

            # Handle array content (possibly multimodal)
            elif isinstance(msg["content"], list):
                parts = []
                for content in msg["content"]:
                    ctype = content.get("type")
                    if ctype == "text":
                        parts.append({"text": content["text"]})
                    elif ctype == "image_url":
                        image_url = content.get("image_url", {}).get("url")
                        if not image_url:
                            continue
                        if image_url.startswith("data:"):
                            # Inline base64 data image
                            prefix, b64data = image_url.split(",", 1)
                            mime_type = prefix.split(":")[1].split(";")[0]
                            parts.append({"inlineData": {"mimeType": mime_type, "data": b64data}})
                        else:
                            parts.append(
                                {
                                    "fileData": {
                                        "mimeType": "image/jpeg",  # Could improve by validation
                                        "fileUri": image_url,
                                    }
                                }
                            )
            else:
                parts = [{"text": str(msg["content"])}]
            format_messages.append({"role": role, "parts": parts})
        if media:
            if not format_messages:
                format_messages.append({"role": "user", "parts": []})
            for media_data, filename in media:
                if isinstance(media_data, str):
                    if not filename:
                        filename = media_data
                    extension = filename.split(".")[-1].replace("jpg", "jpeg")
                    format_messages[-1]["parts"].append(
                        {
                            "fileData": {
                                "mimeType": f"image/{extension}",
                                "fileUri": image_url,
                            }
                        }
                    )
                else:
                    media_data = to_bytes(media_data)
                    format_messages[-1]["parts"].append({
                        "inlineData": {
                            "mimeType": is_data_an_media(media_data, filename),
                            "data": base64.b64encode(media_data).decode()
                        }
                    })
        return format_messages