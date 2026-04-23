def _generate_dispatched(
        self,
        messages: list = None,
        system_prompt: str = "",
        image = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        min_p: float = 0.0,
        max_new_tokens: int = 256,
        repetition_penalty: float = 1.0,
        cancel_event = None,
        use_adapter = None,
    ) -> Generator[str, None, None]:
        """Dispatched generation — sends command without holding _gen_lock.

        Uses a per-request mailbox to receive tokens. This allows two
        compare-mode requests to be queued in the subprocess simultaneously,
        eliminating the inter-generation round-trip overhead.

        The subprocess processes commands sequentially from its cmd_queue,
        so generation is still serialized at the GPU level — we just avoid
        the orchestrator-level lock contention.
        """
        if not self._ensure_subprocess_alive():
            yield "Error: Inference subprocess is not running"
            return

        if not self.active_model_name:
            yield "Error: No active model"
            return

        # Ensure dispatcher is running
        self._start_dispatcher()

        request_id = str(uuid.uuid4())

        # Convert PIL Image to base64 if needed
        image_b64 = None
        if image is not None:
            image_b64 = self._pil_to_base64(image)

        cmd = {
            "type": "generate",
            "request_id": request_id,
            "messages": messages or [],
            "system_prompt": system_prompt,
            "image_base64": image_b64,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "min_p": min_p,
            "max_new_tokens": max_new_tokens,
            "repetition_penalty": repetition_penalty,
        }

        if use_adapter is not None:
            cmd["use_adapter"] = use_adapter

        # Create mailbox BEFORE sending command
        mailbox: queue.Queue = queue.Queue()
        with self._mailbox_lock:
            self._mailboxes[request_id] = mailbox

        try:
            self._send_cmd(cmd)
        except RuntimeError as exc:
            with self._mailbox_lock:
                self._mailboxes.pop(request_id, None)
            yield f"Error: {exc}"
            return

        # Read tokens from our private mailbox
        try:
            while True:
                try:
                    resp = mailbox.get(timeout = _DISPATCH_READ_TIMEOUT)
                except queue.Empty:
                    # Timeout — check subprocess health
                    if not self._ensure_subprocess_alive():
                        yield "Error: Inference subprocess crashed during generation"
                        return
                    continue

                rtype = resp.get("type", "")

                if rtype == "token":
                    # Check cancel from route (e.g. SSE connection closed)
                    if cancel_event is not None and cancel_event.is_set():
                        self._cancel_generation()
                        # Drain remaining events for this request
                        self._drain_mailbox(mailbox, timeout = 5.0)
                        return
                    yield resp.get("text", "")

                elif rtype == "gen_done":
                    return

                elif rtype == "gen_error":
                    yield f"Error: {resp.get('error', 'Unknown error')}"
                    return
        finally:
            with self._mailbox_lock:
                self._mailboxes.pop(request_id, None)