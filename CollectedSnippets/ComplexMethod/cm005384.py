def get_processor_inputs_from_messages(messages: list[dict], modality: Modality) -> list[dict]:
        """Convert OpenAI-format messages to the format expected by HF processors.

        All modalities extract text. VLM additionally handles ``image_url`` and ``video_url``.
        MULTIMODAL handles all of the above plus ``input_audio`` and ``audio_url``.
        For LLMs, the content parts are collapsed into a plain text string.

        Args:
            messages (`list[dict]`): OpenAI-format chat messages.
            modality (`Modality`): The model modality (LLM, VLM, or MULTIMODAL).

        Returns:
            `list[dict]`: Processor-compatible messages.
        """
        processor_inputs = []

        for message in messages:
            parsed = {"role": message["role"], "content": []}

            # Forward tool-use fields so apply_chat_template can handle multi-turn tool conversations
            if "tool_calls" in message:
                parsed["tool_calls"] = message["tool_calls"]
            if "tool_call_id" in message:
                parsed["tool_call_id"] = message["tool_call_id"]

            # When tool_calls are present, ignore content — it's either empty or contains
            # raw tool call markup that would confuse the chat template if rendered.
            raw_content = [] if "tool_calls" in message else (message.get("content") or [])
            if isinstance(raw_content, str):
                raw_content = [{"type": "text", "text": raw_content}]

            for content in raw_content:
                content_type = content["type"]
                # Text: chat completions ("text") and Responses API ("input_text")
                if content_type in ("text", "input_text", "output_text"):
                    parsed["content"].append({"type": "text", "text": content["text"]})
                # Image: chat completions ("image_url") and Responses API ("input_image")
                elif content_type in ("image_url", "input_image") and modality in (Modality.VLM, Modality.MULTIMODAL):
                    # chat completions: {"image_url": {"url": "..."}}, Responses API: {"image_url": "..."}
                    url = content["image_url"]
                    if isinstance(url, dict):
                        url = url["url"]
                    parsed["content"].append({"type": "image", "url": url})
                # Audio: unlike images, load_audio doesn't accept raw base64 — wrap as a data URI
                elif content_type == "input_audio" and modality == Modality.MULTIMODAL:
                    input_audio = content["input_audio"]
                    fmt = input_audio.get("format", "wav") if isinstance(input_audio, dict) else "wav"
                    audio_b64 = input_audio["data"]
                    parsed["content"].append({"type": "audio", "url": f"data:audio/{fmt};base64,{audio_b64}"})
                # Extensions (not part of the OpenAI API standard)
                elif content_type == "video_url" and modality in (Modality.VLM, Modality.MULTIMODAL):
                    parsed["content"].append({"type": "video", "url": content["video_url"]["url"]})
                elif content_type == "audio_url" and modality == Modality.MULTIMODAL:
                    parsed["content"].append({"type": "audio", "url": content["audio_url"]["url"]})

            # LLMs expect plain text, not a list of content parts
            if modality == Modality.LLM:
                parsed["content"] = " ".join(c["text"] for c in parsed["content"])

            processor_inputs.append(parsed)
        return processor_inputs