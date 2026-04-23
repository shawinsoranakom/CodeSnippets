def _generate_locked(
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
        """Actual generation logic — must be called under _gen_lock."""
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

        try:
            self._send_cmd(cmd)
        except RuntimeError as exc:
            yield f"Error: {exc}"
            return

        # Yield tokens from response queue — we are the only reader
        # because _gen_lock is held.
        while True:
            resp = self._read_resp(timeout = 30.0)

            if resp is None:
                # Check subprocess health
                if not self._ensure_subprocess_alive():
                    yield "Error: Inference subprocess crashed during generation"
                    return
                continue

            rtype = resp.get("type", "")

            # Status messages — skip
            if rtype == "status":
                continue

            # Error without request_id = subprocess-level error
            resp_rid = resp.get("request_id")
            if rtype == "error" and not resp_rid:
                yield f"Error: {resp.get('error', 'Unknown error')}"
                return

            if rtype == "token":
                # Check cancel from route (e.g. SSE connection closed)
                if cancel_event is not None and cancel_event.is_set():
                    self._cancel_generation()
                    # Wait for the subprocess to acknowledge cancellation
                    # (gen_done/gen_error) so stale events don't leak into
                    # the next generation request.
                    self._drain_until_gen_done(timeout = 5.0)
                    return
                yield resp.get("text", "")

            elif rtype == "gen_done":
                return

            elif rtype == "gen_error":
                yield f"Error: {resp.get('error', 'Unknown error')}"
                return