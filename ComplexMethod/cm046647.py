def _generate_audio_input_inner(
        self,
        audio_array,
        audio_type: Optional[str] = None,
        messages: list = None,
        system_prompt: str = "",
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        min_p: float = 0.0,
        max_new_tokens: int = 512,
        repetition_penalty: float = 1.0,
        cancel_event = None,
    ) -> Generator[str, None, None]:
        """Shared inner logic for audio input generation (Whisper + ASR)."""
        if not self._ensure_subprocess_alive():
            yield "Error: Inference subprocess is not running"
            return
        if not self.active_model_name:
            yield "Error: No active model"
            return

        with self._gen_lock:
            import uuid

            request_id = str(uuid.uuid4())

            # Convert numpy array to list for mp.Queue serialization
            audio_data = (
                audio_array.tolist()
                if hasattr(audio_array, "tolist")
                else list(audio_array)
            )

            cmd = {
                "type": "generate_audio_input",
                "request_id": request_id,
                "audio_data": audio_data,
                "audio_type": audio_type,
                "messages": messages or [],
                "system_prompt": system_prompt,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "min_p": min_p,
                "max_new_tokens": max_new_tokens,
                "repetition_penalty": repetition_penalty,
            }

            try:
                self._send_cmd(cmd)
            except RuntimeError as exc:
                yield f"Error: {exc}"
                return

            # Yield tokens — same pattern as _generate_locked
            while True:
                resp = self._read_resp(timeout = 30.0)

                if resp is None:
                    if not self._ensure_subprocess_alive():
                        yield "Error: Inference subprocess crashed during audio input generation"
                        return
                    continue

                rtype = resp.get("type", "")

                if rtype == "status":
                    continue

                if rtype == "error" and not resp.get("request_id"):
                    yield f"Error: {resp.get('error', 'Unknown error')}"
                    return

                if rtype == "token":
                    if cancel_event is not None and cancel_event.is_set():
                        self._cancel_generation()
                        self._drain_until_gen_done(timeout = 5.0)
                        return
                    yield resp.get("text", "")

                elif rtype == "gen_done":
                    return

                elif rtype == "gen_error":
                    yield f"Error: {resp.get('error', 'Unknown error')}"
                    return