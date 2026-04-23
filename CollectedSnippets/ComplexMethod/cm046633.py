def generate_chat_completion_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
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
        max_tool_iterations: int = 25,
        auto_heal_tool_calls: bool = True,
        tool_call_timeout: int = 300,
        session_id: Optional[str] = None,
    ) -> Generator[dict, None, None]:
        """
        Agentic loop: let the model call tools, execute them, and continue.

        Yields dicts with:
          {"type": "status", "text": "Searching: ..."/"Reading: ..."}   -- tool status updates
          {"type": "content", "text": "token"}            -- streamed content tokens (cumulative)
          {"type": "reasoning", "text": "token"}          -- streamed reasoning tokens (cumulative)
        """
        from core.inference.tools import execute_tool

        if not self.is_loaded:
            raise RuntimeError("llama-server is not loaded")

        conversation = list(messages)
        url = f"{self.base_url}/v1/chat/completions"
        _accumulated_completion_tokens = 0
        _accumulated_predicted_ms = 0.0
        _accumulated_predicted_n = 0

        def _strip_tool_markup(text: str, *, final: bool = False) -> str:
            if not auto_heal_tool_calls:
                return text
            patterns = _TOOL_ALL_PATS if final else _TOOL_CLOSED_PATS
            for pat in patterns:
                text = pat.sub("", text)
            return text.strip() if final else text

        # XML prefixes that signal a tool call in content.
        # Empty when auto_heal is disabled so the buffer never
        # speculatively holds content for XML detection.
        _TOOL_XML_SIGNALS = (
            ("<tool_call>", "<function=") if auto_heal_tool_calls else ()
        )
        _MAX_BUFFER_CHARS = 32

        # ── Duplicate tool-call detection ────────────────────────
        # Track recent (tool_name, arguments) hashes to detect loops
        # where the model repeats the exact same call.  Retries after
        # a transient failure are allowed (only block when the previous
        # identical call succeeded).
        _tool_call_history: list[tuple[str, bool]] = []  # (key, failed)

        # ── Re-prompt on plan-without-action ─────────────────
        # When the model describes what it intends to do (forward-looking
        # language) without actually calling a tool, re-prompt once.
        # Only triggers on responses that signal intent/planning -- a
        # direct answer like "4" or "Hello!" will not match.
        # Pattern is compiled once at module level (_INTENT_SIGNAL).
        _reprompt_count = 0

        # Reserve extra iterations for re-prompts so they don't
        # consume the caller's tool-call budget.  Only add the
        # extra slot when tool iterations are actually allowed.
        _extra = _MAX_REPROMPTS if max_tool_iterations > 0 else 0
        for iteration in range(max_tool_iterations + _extra):
            if cancel_event is not None and cancel_event.is_set():
                return

            # Build payload -- stream: True so we detect tool signals
            # in the first 1-2 chunks without a non-streaming penalty.
            payload = {
                "messages": conversation,
                "stream": True,
                "stream_options": {"include_usage": True},
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k if top_k >= 0 else 0,
                "min_p": min_p,
                "repeat_penalty": repetition_penalty,
                "presence_penalty": presence_penalty,
                "tools": tools,
                "tool_choice": "auto",
            }
            if self._supports_reasoning and enable_thinking is not None:
                payload["chat_template_kwargs"] = {"enable_thinking": enable_thinking}
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if stop:
                payload["stop"] = stop

            try:
                _auth_headers = (
                    {"Authorization": f"Bearer {self._api_key}"}
                    if self._api_key
                    else None
                )

                # ── Speculative buffer state machine ──────────────────
                # BUFFERING: accumulating content, checking for tool signals
                # STREAMING: no tool detected, yielding tokens to caller
                # DRAINING:  tool signal found, silently consuming rest
                _S_BUFFERING = 0
                _S_STREAMING = 1
                _S_DRAINING = 2

                detect_state = _S_BUFFERING
                content_buffer = ""  # Raw content held during BUFFERING
                content_accum = ""  # All content tokens (for tool parsing)
                reasoning_accum = ""
                cumulative_display = ""  # Cumulative text yielded (with <think>)
                in_thinking = False
                has_content_tokens = False
                tool_calls_acc = {}  # Structured delta.tool_calls fragments
                has_structured_tc = False
                _iter_usage = None
                _iter_timings = None
                _stream_done = False
                _last_emitted = ""

                stream_timeout = httpx.Timeout(
                    connect = 10,
                    read = 0.5,
                    write = 10,
                    pool = 10,
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
                                f"llama-server returned {response.status_code}: "
                                f"{error_body}"
                            )

                        raw_buf = ""
                        for raw_chunk in self._iter_text_cancellable(
                            response,
                            cancel_event,
                        ):
                            raw_buf += raw_chunk
                            while "\n" in raw_buf:
                                line, raw_buf = raw_buf.split("\n", 1)
                                line = line.strip()

                                if not line:
                                    continue
                                if line == "data: [DONE]":
                                    # Flush thinking state for STREAMING
                                    if detect_state == _S_STREAMING and in_thinking:
                                        if has_content_tokens:
                                            cumulative_display += "</think>"
                                            yield {
                                                "type": "content",
                                                "text": _strip_tool_markup(
                                                    cumulative_display,
                                                    final = True,
                                                ),
                                            }
                                        else:
                                            cumulative_display = reasoning_accum
                                            yield {
                                                "type": "content",
                                                "text": cumulative_display,
                                            }
                                    _stream_done = True
                                    break  # exit inner while
                                if not line.startswith("data: "):
                                    continue

                                try:
                                    chunk_data = json.loads(line[6:])
                                    _ct = chunk_data.get("timings")
                                    if _ct:
                                        _iter_timings = _ct
                                    _cu = chunk_data.get("usage")
                                    if _cu:
                                        _iter_usage = _cu

                                    choices = chunk_data.get("choices", [])
                                    if not choices:
                                        continue

                                    delta = choices[0].get("delta", {})

                                    # ── Structured tool_calls ──
                                    tc_deltas = delta.get("tool_calls")
                                    if tc_deltas:
                                        # Once visible content has been
                                        # emitted, do not reclassify this
                                        # turn as a tool call.
                                        if _last_emitted:
                                            continue
                                        has_structured_tc = True
                                        detect_state = _S_DRAINING
                                        for tc_d in tc_deltas:
                                            idx = tc_d.get("index", 0)
                                            if idx not in tool_calls_acc:
                                                tool_calls_acc[idx] = {
                                                    "id": tc_d.get("id", f"call_{idx}"),
                                                    "type": "function",
                                                    "function": {
                                                        "name": "",
                                                        "arguments": "",
                                                    },
                                                }
                                            elif tc_d.get("id"):
                                                # Update ID if real one
                                                # arrives on a later delta
                                                tool_calls_acc[idx]["id"] = tc_d["id"]
                                            func = tc_d.get("function", {})
                                            if func.get("name"):
                                                tool_calls_acc[idx]["function"][
                                                    "name"
                                                ] += func["name"]
                                            if func.get("arguments"):
                                                tool_calls_acc[idx]["function"][
                                                    "arguments"
                                                ] += func["arguments"]
                                        continue

                                    # ── Reasoning tokens ──
                                    # Only yield in STREAMING state. In BUFFERING
                                    # and DRAINING, accumulate silently so we don't
                                    # corrupt the consumer's prev_text tracker
                                    # (routes/inference.py never resets prev_text
                                    # between tool iterations).
                                    reasoning = delta.get("reasoning_content", "")
                                    if reasoning:
                                        reasoning_accum += reasoning
                                        if detect_state == _S_STREAMING:
                                            if not in_thinking:
                                                cumulative_display += "<think>"
                                                in_thinking = True
                                            cumulative_display += reasoning
                                            yield {
                                                "type": "content",
                                                "text": cumulative_display,
                                            }

                                    # ── Content tokens ──
                                    token = delta.get("content", "")
                                    if token:
                                        has_content_tokens = True
                                        content_accum += token

                                        if detect_state == _S_DRAINING:
                                            pass  # accumulate silently

                                        elif detect_state == _S_STREAMING:
                                            if in_thinking:
                                                cumulative_display += "</think>"
                                                in_thinking = False
                                            cumulative_display += token
                                            cleaned = _strip_tool_markup(
                                                cumulative_display,
                                            )
                                            if len(cleaned) > len(_last_emitted):
                                                _last_emitted = cleaned
                                                yield {
                                                    "type": "content",
                                                    "text": cleaned,
                                                }

                                        elif detect_state == _S_BUFFERING:
                                            content_buffer += token
                                            stripped_buf = content_buffer.lstrip()
                                            if not stripped_buf:
                                                continue

                                            # Check tool signal prefixes
                                            is_prefix = False
                                            is_match = False
                                            for sig in _TOOL_XML_SIGNALS:
                                                if stripped_buf.startswith(sig):
                                                    is_match = True
                                                    break
                                                if sig.startswith(stripped_buf):
                                                    is_prefix = True
                                                    break

                                            if is_match:
                                                detect_state = _S_DRAINING
                                            elif (
                                                is_prefix
                                                and len(stripped_buf)
                                                < _MAX_BUFFER_CHARS
                                            ):
                                                pass  # keep buffering
                                            else:
                                                # Not a tool -- flush buffer
                                                detect_state = _S_STREAMING
                                                # Flush any reasoning accumulated
                                                # during BUFFERING phase
                                                if reasoning_accum:
                                                    cumulative_display += "<think>"
                                                    cumulative_display += (
                                                        reasoning_accum
                                                    )
                                                    cumulative_display += "</think>"
                                                cumulative_display += content_buffer
                                                cleaned = _strip_tool_markup(
                                                    cumulative_display,
                                                )
                                                if len(cleaned) > len(_last_emitted):
                                                    _last_emitted = cleaned
                                                    yield {
                                                        "type": "content",
                                                        "text": cleaned,
                                                    }

                                except json.JSONDecodeError:
                                    logger.debug(
                                        f"Skipping malformed SSE line: " f"{line[:100]}"
                                    )
                            if _stream_done:
                                break  # exit outer for

                # ── Resolve BUFFERING at stream end ──
                if detect_state == _S_BUFFERING:
                    stripped_buf = content_buffer.lstrip()
                    if (
                        stripped_buf
                        and auto_heal_tool_calls
                        and any(s in stripped_buf for s in _TOOL_XML_SIGNALS)
                    ):
                        detect_state = _S_DRAINING
                    elif content_accum or reasoning_accum:
                        detect_state = _S_STREAMING
                        if content_buffer:
                            # Flush any reasoning accumulated first
                            if reasoning_accum:
                                cumulative_display += "<think>"
                                cumulative_display += reasoning_accum
                                cumulative_display += "</think>"
                            cumulative_display += content_buffer
                            yield {
                                "type": "content",
                                "text": _strip_tool_markup(
                                    cumulative_display,
                                    final = True,
                                ),
                            }
                        elif reasoning_accum and not has_content_tokens:
                            # Reasoning-only response (no content tokens):
                            # show reasoning as plain text, matching
                            # the final streaming pass behavior for
                            # models that put everything in reasoning.
                            cumulative_display = reasoning_accum
                            yield {
                                "type": "content",
                                "text": cumulative_display,
                            }
                    else:
                        return

                # ── STREAMING path: no tool call ──
                if detect_state == _S_STREAMING:
                    # Safety net: check for XML tool signals in content.
                    # The route layer resets prev_text on tool_start, so
                    # post-tool synthesis streams correctly even if
                    # content was already emitted before the tool XML.
                    _safety_tc = None
                    if auto_heal_tool_calls and any(
                        s in content_accum for s in _TOOL_XML_SIGNALS
                    ):
                        _safety_tc = self._parse_tool_calls_from_text(
                            content_accum,
                        )
                    if not _safety_tc:
                        # ── Re-prompt on plan-without-action ──
                        # If the model described what it intends to do
                        # (forward-looking language) without calling any
                        # tool, nudge it to act.  Only fires once per
                        # request and only on short responses that
                        # contain intent signals -- a direct answer
                        # like "4" or "Hello!" won't trigger this.
                        # Use content if available, otherwise fall back
                        # to reasoning text (reasoning-only stalls).
                        _stripped = content_accum.strip()
                        if not _stripped:
                            _stripped = reasoning_accum.strip()
                        if (
                            tools
                            and _reprompt_count < _MAX_REPROMPTS
                            and 0 < len(_stripped) < _REPROMPT_MAX_CHARS
                            and _INTENT_SIGNAL.search(_stripped)
                        ):
                            _reprompt_count += 1
                            logger.info(
                                f"Re-prompt {_reprompt_count}/{_MAX_REPROMPTS}: "
                                f"model responded without calling tools "
                                f"({len(_stripped)} chars)"
                            )
                            conversation.append(
                                {
                                    "role": "assistant",
                                    "content": _stripped,
                                }
                            )
                            conversation.append(
                                {
                                    "role": "user",
                                    "content": (
                                        "STOP. Do NOT write code or explain. "
                                        "You MUST call a tool NOW. "
                                        "Call web_search or python immediately."
                                    ),
                                }
                            )
                            # Accumulate tokens and timing from this iteration
                            _fu_r = _iter_usage or {}
                            _accumulated_completion_tokens += _fu_r.get(
                                "completion_tokens", 0
                            )
                            _it_r = _iter_timings or {}
                            _accumulated_predicted_ms += _it_r.get("predicted_ms", 0)
                            _accumulated_predicted_n += _it_r.get("predicted_n", 0)
                            yield {"type": "status", "text": ""}
                            continue

                        # Content was already streamed.  Yield metadata.
                        yield {"type": "status", "text": ""}
                        _fu = _iter_usage or {}
                        _fc = _fu.get("completion_tokens", 0)
                        _fp = _fu.get("prompt_tokens", 0)
                        _tc = _fc + _accumulated_completion_tokens
                        if (
                            _iter_usage
                            or _iter_timings
                            or _accumulated_completion_tokens
                        ):
                            _mt = dict(_iter_timings) if _iter_timings else {}
                            if _accumulated_predicted_ms or _accumulated_predicted_n:
                                _mt["predicted_ms"] = (
                                    _mt.get("predicted_ms", 0)
                                    + _accumulated_predicted_ms
                                )
                                _tn = (
                                    _mt.get("predicted_n", 0) + _accumulated_predicted_n
                                )
                                _mt["predicted_n"] = _tn
                                _tms = _mt["predicted_ms"]
                                if _tms > 0:
                                    _mt["predicted_per_second"] = _tn / (_tms / 1000.0)
                            yield {
                                "type": "metadata",
                                "usage": {
                                    "prompt_tokens": _fp,
                                    "completion_tokens": _tc,
                                    "total_tokens": _fp + _tc,
                                },
                                "timings": _mt,
                            }
                        return

                    # Safety net caught tool XML -- treat as tool call
                    tool_calls = _safety_tc
                    content_text = _strip_tool_markup(
                        content_accum,
                        final = True,
                    )
                    logger.info(
                        f"Safety net: parsed {len(tool_calls)} tool call(s) "
                        f"from streamed content"
                    )
                else:
                    # ── DRAINING path: assemble tool_calls ──
                    tool_calls = None
                    content_text = content_accum
                    if has_structured_tc:
                        # Filter out incomplete fragments (e.g. from
                        # truncation by max_tokens or disconnect).
                        tool_calls = [
                            tool_calls_acc[i]
                            for i in sorted(tool_calls_acc)
                            if (
                                tool_calls_acc[i]
                                .get("function", {})
                                .get("name", "")
                                .strip()
                            )
                        ] or None
                    if (
                        not tool_calls
                        and auto_heal_tool_calls
                        and any(s in content_accum for s in _TOOL_XML_SIGNALS)
                    ):
                        tool_calls = self._parse_tool_calls_from_text(
                            content_accum,
                        )
                    if tool_calls and not has_structured_tc:
                        content_text = _strip_tool_markup(
                            content_text,
                            final = True,
                        )
                    if tool_calls:
                        logger.info(
                            f"Parsed {len(tool_calls)} tool call(s) from "
                            f"{'structured delta' if has_structured_tc else 'content text'}"
                        )
                    if not tool_calls:
                        # DRAINING but no tool calls (false positive).
                        # Merge accumulated metrics from prior tool
                        # iterations so they are not silently dropped.
                        yield {"type": "status", "text": ""}
                        if content_accum:
                            # Strip leaked tool-call XML before yielding
                            content_accum = _strip_tool_markup(
                                content_accum, final = True
                            )
                        if content_accum:
                            yield {"type": "content", "text": content_accum}
                        _fu = _iter_usage or {}
                        _fc = _fu.get("completion_tokens", 0)
                        _fp = _fu.get("prompt_tokens", 0)
                        _tc = _fc + _accumulated_completion_tokens
                        if (
                            _iter_usage
                            or _iter_timings
                            or _accumulated_completion_tokens
                        ):
                            _mt = dict(_iter_timings) if _iter_timings else {}
                            if _accumulated_predicted_ms or _accumulated_predicted_n:
                                _mt["predicted_ms"] = (
                                    _mt.get("predicted_ms", 0)
                                    + _accumulated_predicted_ms
                                )
                                _tn = (
                                    _mt.get("predicted_n", 0) + _accumulated_predicted_n
                                )
                                _mt["predicted_n"] = _tn
                                _tms = _mt["predicted_ms"]
                                if _tms > 0:
                                    _mt["predicted_per_second"] = _tn / (_tms / 1000.0)
                            yield {
                                "type": "metadata",
                                "usage": {
                                    "prompt_tokens": _fp,
                                    "completion_tokens": _tc,
                                    "total_tokens": _fp + _tc,
                                },
                                "timings": _mt,
                            }
                        return

                # ── Execute tool calls ──
                _accumulated_completion_tokens += (_iter_usage or {}).get(
                    "completion_tokens", 0
                )
                _it = _iter_timings or {}
                _accumulated_predicted_ms += _it.get("predicted_ms", 0)
                _accumulated_predicted_n += _it.get("predicted_n", 0)

                assistant_msg = {"role": "assistant", "content": content_text}
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                conversation.append(assistant_msg)

                for tc in tool_calls or []:
                    func = tc.get("function", {})
                    tool_name = func.get("name", "")
                    raw_args = func.get("arguments", {})

                    if isinstance(raw_args, str):
                        try:
                            arguments = json.loads(raw_args)
                        except (json.JSONDecodeError, ValueError):
                            if auto_heal_tool_calls:
                                arguments = {"query": raw_args}
                            else:
                                arguments = {"raw": raw_args}
                    else:
                        arguments = raw_args

                    if tool_name == "web_search":
                        _ws_url = (arguments.get("url") or "").strip()
                        if _ws_url:
                            _parsed = urlparse(_ws_url)
                            if _parsed.scheme in ("http", "https") and _parsed.hostname:
                                _ws_host = _parsed.hostname
                                if _ws_host.startswith("www."):
                                    _ws_host = _ws_host[4:]
                                status_text = f"Reading: {_ws_host}"
                            else:
                                status_text = "Reading page..."
                        else:
                            status_text = f"Searching: {arguments.get('query', '')}"
                    elif tool_name == "python":
                        preview = (
                            (arguments.get("code") or "").strip().split("\n")[0][:60]
                        )
                        status_text = (
                            f"Running Python: {preview}"
                            if preview
                            else "Running Python..."
                        )
                    elif tool_name == "terminal":
                        cmd_preview = (arguments.get("command") or "")[:60]
                        status_text = (
                            f"Running: {cmd_preview}"
                            if cmd_preview
                            else "Running command..."
                        )
                    else:
                        status_text = f"Calling: {tool_name}"
                    yield {"type": "status", "text": status_text}

                    yield {
                        "type": "tool_start",
                        "tool_name": tool_name,
                        "tool_call_id": tc.get("id", ""),
                        "arguments": arguments,
                    }

                    # ── Duplicate call detection ──────────────
                    # str(dict) is stable here: arguments always comes from
                    # json.loads on the same model output within one request,
                    # so insertion order is deterministic (Python 3.7+).
                    _tc_key = tool_name + str(arguments)
                    _prev = _tool_call_history[-1] if _tool_call_history else None
                    if _prev and _prev[0] == _tc_key and not _prev[1]:
                        result = (
                            "You already made this exact call. "
                            "Do not repeat the same tool call. "
                            "Try a different approach: fetch a URL "
                            "from previous results, use Python to "
                            "process data you already have, or "
                            "provide your final answer now."
                        )
                    else:
                        _effective_timeout = (
                            None if tool_call_timeout >= 9999 else tool_call_timeout
                        )
                        result = execute_tool(
                            tool_name,
                            arguments,
                            cancel_event = cancel_event,
                            timeout = _effective_timeout,
                            session_id = session_id,
                        )

                    yield {
                        "type": "tool_end",
                        "tool_name": tool_name,
                        "tool_call_id": tc.get("id", ""),
                        "result": result,
                    }

                    # Nudge model to try a different approach on errors
                    _error_prefixes = (
                        "Error",
                        "Search failed",
                        "Execution error",
                        "Blocked:",
                        "Exit code",
                        "Failed to fetch",
                        "Failed to resolve",
                        "No query provided",
                    )
                    _is_error = isinstance(result, str) and result.lstrip().startswith(
                        _error_prefixes
                    )
                    _tool_call_history.append((_tc_key, _is_error))
                    # Strip image sentinel before feeding result to the LLM
                    # (the full result with sentinel is still yielded via
                    # tool_end so the frontend can extract image paths).
                    _result_content = result
                    if "\n__IMAGES__:" in _result_content:
                        _result_content = _result_content.rsplit("\n__IMAGES__:", 1)[0]
                    if _is_error:
                        _result_content = (
                            _result_content + "\n\nThe tool call encountered an issue. "
                            "Please try a different approach or rephrase your request."
                        )

                    tool_msg = {
                        "role": "tool",
                        "name": tool_name,
                        "content": _result_content,
                    }
                    tool_call_id = tc.get("id")
                    if tool_call_id:
                        tool_msg["tool_call_id"] = tool_call_id
                    conversation.append(tool_msg)

                # Clear tool status badge before next generation iteration
                yield {"type": "status", "text": ""}
                # Continue the loop to let model respond with context
                continue

            except httpx.ConnectError:
                raise RuntimeError("Lost connection to llama-server")
            except Exception as e:
                if cancel_event is not None and cancel_event.is_set():
                    return
                raise

        # ── Tool iteration cap reached -- synthesize final answer ──
        # The model used all iterations without producing a final text
        # response. Inject a nudge so the final streaming pass produces
        # a useful answer instead of continuing to request tools.
        if max_tool_iterations > 0:
            conversation.append(
                {
                    "role": "user",
                    "content": (
                        "You have used all available tool calls. Based on "
                        "everything you have found so far, provide your final "
                        "answer now. Do not call any more tools."
                    ),
                }
            )

        # Clear status
        yield {"type": "status", "text": ""}

        # Final streaming pass with the full conversation context
        stream_payload = {
            "messages": conversation,
            "stream": True,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k if top_k >= 0 else 0,
            "min_p": min_p,
            "repeat_penalty": repetition_penalty,
            "presence_penalty": presence_penalty,
        }
        if self._supports_reasoning and enable_thinking is not None:
            stream_payload["chat_template_kwargs"] = {
                "enable_thinking": enable_thinking
            }
        if max_tokens is not None:
            stream_payload["max_tokens"] = max_tokens
        if stop:
            stream_payload["stop"] = stop
        stream_payload["stream_options"] = {"include_usage": True}

        cumulative = ""
        _last_emitted = ""
        in_thinking = False
        has_content_tokens = False
        reasoning_text = ""
        _metadata_usage = None
        _metadata_timings = None
        _stream_done = False

        try:
            stream_timeout = httpx.Timeout(connect = 10, read = 0.5, write = 10, pool = 10)
            _auth_headers = (
                {"Authorization": f"Bearer {self._api_key}"} if self._api_key else None
            )
            with httpx.Client(timeout = stream_timeout) as client:
                with self._stream_with_retry(
                    client,
                    url,
                    stream_payload,
                    cancel_event,
                    headers = _auth_headers,
                ) as response:
                    if response.status_code != 200:
                        error_body = response.read().decode()
                        raise RuntimeError(
                            f"llama-server returned {response.status_code}: {error_body}"
                        )

                    buffer = ""
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
                                        cumulative += "</think>"
                                        yield {
                                            "type": "content",
                                            "text": _strip_tool_markup(
                                                cumulative, final = True
                                            ),
                                        }
                                    else:
                                        cumulative = reasoning_text
                                        yield {"type": "content", "text": cumulative}
                                _stream_done = True
                                break  # exit inner while
                            if not line.startswith("data: "):
                                continue

                            try:
                                chunk_data = json.loads(line[6:])
                                # Capture server timings/usage from final chunks
                                _chunk_timings = chunk_data.get("timings")
                                if _chunk_timings:
                                    _metadata_timings = _chunk_timings
                                _chunk_usage = chunk_data.get("usage")
                                if _chunk_usage:
                                    _metadata_usage = _chunk_usage
                                choices = chunk_data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})

                                    reasoning = delta.get("reasoning_content", "")
                                    if reasoning:
                                        reasoning_text += reasoning
                                        if not in_thinking:
                                            cumulative += "<think>"
                                            in_thinking = True
                                        cumulative += reasoning
                                        yield {"type": "content", "text": cumulative}

                                    token = delta.get("content", "")
                                    if token:
                                        has_content_tokens = True
                                        if in_thinking:
                                            cumulative += "</think>"
                                            in_thinking = False
                                        cumulative += token
                                        cleaned = _strip_tool_markup(cumulative)
                                        # Only emit when cleaned text grows (monotonic).
                                        if len(cleaned) > len(_last_emitted):
                                            _last_emitted = cleaned
                                            yield {"type": "content", "text": cleaned}
                            except json.JSONDecodeError:
                                logger.debug(
                                    f"Skipping malformed SSE line: {line[:100]}"
                                )
                        if _stream_done:
                            break  # exit outer for
                    _final_usage = _metadata_usage or {}
                    _final_completion = _final_usage.get("completion_tokens", 0)
                    _final_prompt = _final_usage.get("prompt_tokens", 0)
                    _total_completion = (
                        _final_completion + _accumulated_completion_tokens
                    )
                    if _metadata_usage or _metadata_timings:
                        _merged_timings = (
                            dict(_metadata_timings) if _metadata_timings else {}
                        )
                        if _accumulated_predicted_ms or _accumulated_predicted_n:
                            _merged_timings["predicted_ms"] = (
                                _merged_timings.get("predicted_ms", 0)
                                + _accumulated_predicted_ms
                            )
                            _total_predicted_n = (
                                _merged_timings.get("predicted_n", 0)
                                + _accumulated_predicted_n
                            )
                            _merged_timings["predicted_n"] = _total_predicted_n
                            _total_predicted_ms = _merged_timings["predicted_ms"]
                            if _total_predicted_ms > 0:
                                _merged_timings["predicted_per_second"] = (
                                    _total_predicted_n / (_total_predicted_ms / 1000.0)
                                )
                        yield {
                            "type": "metadata",
                            "usage": {
                                "prompt_tokens": _final_prompt,
                                "completion_tokens": _total_completion,
                                "total_tokens": _final_prompt + _total_completion,
                            },
                            "timings": _merged_timings,
                        }

        except httpx.ConnectError:
            raise RuntimeError("Lost connection to llama-server")
        except Exception as e:
            if cancel_event is not None and cancel_event.is_set():
                return
            raise