def generate_chat_completion(
        self,
        messages: list[dict],
        image_b64: Optional[str] = None,
        temperature: float = 0.6,
        top_p: float = 0.95,
        top_k: int = 20,
        min_p: float = 0.01,
        max_tokens: Optional[int] = None,
        repetition_penalty: float = 1.0,
        presence_penalty: float = 0.0,
        stop: Optional[list[str]] = None,
        cancel_event: Optional[threading.Event] = None,
        enable_thinking: Optional[bool] = None,
    ) -> Generator[str | dict, None, None]:
        """
        Send a chat completion request to llama-server and stream tokens back.

        Uses /v1/chat/completions — llama-server handles chat template
        application and vision (multimodal image_url parts) natively.

        Yields cumulative text (matching InferenceBackend's convention).
        """
        if not self.is_loaded:
            raise RuntimeError("llama-server is not loaded")

        openai_messages = self._build_openai_messages(messages, image_b64)

        payload = {
            "messages": openai_messages,
            "stream": True,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k if top_k >= 0 else 0,
            "min_p": min_p,
            "repeat_penalty": repetition_penalty,
            "presence_penalty": presence_penalty,
        }
        # Pass enable_thinking per-request for reasoning models
        if self._supports_reasoning and enable_thinking is not None:
            payload["chat_template_kwargs"] = {"enable_thinking": enable_thinking}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if stop:
            payload["stop"] = stop
        payload["stream_options"] = {"include_usage": True}

        url = f"{self.base_url}/v1/chat/completions"
        cumulative = ""
        in_thinking = False
        _stream_done = False
        _metadata_usage = None
        _metadata_timings = None

        try:
            # _stream_with_retry uses a 120 s read timeout so prefill
            # can finish.  Cancel during streaming is handled by the
            # watcher thread (closes the response on cancel_event).
            stream_timeout = httpx.Timeout(connect = 10, read = 0.5, write = 10, pool = 10)
            _auth_headers = (
                {"Authorization": f"Bearer {self._api_key}"} if self._api_key else None
            )
            with httpx.Client(timeout = stream_timeout) as client:
                with self._stream_with_retry(
                    client,
                    url,
                    payload,
                    cancel_event,
                    headers = _auth_headers,
                ) as response:
                    if response.status_code != 200:
                        error_body = response.read().decode()
                        raise RuntimeError(
                            f"llama-server returned {response.status_code}: {error_body}"
                        )

                    buffer = ""
                    has_content_tokens = False
                    reasoning_text = ""
                    for raw_chunk in self._iter_text_cancellable(
                        response, cancel_event
                    ):
                        buffer += raw_chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()

                            if not line:
                                continue
                            if line == "data: [DONE]":
                                if in_thinking:
                                    if has_content_tokens:
                                        # Real thinking + content: close the tag
                                        cumulative += "</think>"
                                        yield cumulative
                                    else:
                                        # Only reasoning_content, no content tokens:
                                        # the model put its entire reply in reasoning
                                        # (e.g. Qwen3 always-think mode). Show it
                                        # as the main response, not as a thinking block.
                                        cumulative = reasoning_text
                                        yield cumulative
                                _stream_done = True
                                break  # exit inner while
                            if not line.startswith("data: "):
                                continue

                            try:
                                data = json.loads(line[6:])
                                # Capture server timings/usage from final chunks
                                _chunk_timings = data.get("timings")
                                if _chunk_timings:
                                    _metadata_timings = _chunk_timings
                                _chunk_usage = data.get("usage")
                                if _chunk_usage:
                                    _metadata_usage = _chunk_usage
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})

                                    # Handle reasoning/thinking tokens
                                    # llama-server sends these as "reasoning_content"
                                    # Wrap in <think> tags for the frontend parser
                                    reasoning = delta.get("reasoning_content", "")
                                    if reasoning:
                                        reasoning_text += reasoning
                                        if not in_thinking:
                                            cumulative += "<think>"
                                            in_thinking = True
                                        cumulative += reasoning
                                        yield cumulative

                                    token = delta.get("content", "")
                                    if token:
                                        has_content_tokens = True
                                        if in_thinking:
                                            cumulative += "</think>"
                                            in_thinking = False
                                        cumulative += token
                                        yield cumulative
                            except json.JSONDecodeError:
                                logger.debug(
                                    f"Skipping malformed SSE line: {line[:100]}"
                                )
                        if _stream_done:
                            break  # exit outer for
                    if _metadata_usage or _metadata_timings:
                        yield {
                            "type": "metadata",
                            "usage": _metadata_usage,
                            "timings": _metadata_timings,
                        }

        except httpx.ConnectError:
            raise RuntimeError("Lost connection to llama-server")
        except Exception as e:
            if cancel_event is not None and cancel_event.is_set():
                return
            raise