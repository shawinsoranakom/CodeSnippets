def generate_audio_response(
        self,
        text: str,
        temperature: float = 0.6,
        top_p: float = 0.95,
        top_k: int = 50,
        min_p: float = 0.0,
        max_new_tokens: int = 2048,
        repetition_penalty: float = 1.0,
        use_adapter: Optional[Union[bool, str]] = None,
    ) -> Tuple[bytes, int]:
        """Generate TTS audio. Returns (wav_bytes, sample_rate).

        Blocking — sends command and waits for the complete audio response.
        """
        if not self._ensure_subprocess_alive():
            raise RuntimeError("Inference subprocess is not running")
        if not self.active_model_name:
            raise RuntimeError("No active model")

        import uuid

        request_id = str(uuid.uuid4())

        cmd = {
            "type": "generate_audio",
            "request_id": request_id,
            "text": text,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "min_p": min_p,
            "max_new_tokens": max_new_tokens,
            "repetition_penalty": repetition_penalty,
        }
        if use_adapter is not None:
            cmd["use_adapter"] = use_adapter

        self._send_cmd(cmd)

        # Wait for audio_done or audio_error
        deadline = time.monotonic() + 120.0
        while time.monotonic() < deadline:
            remaining = max(0.1, deadline - time.monotonic())
            resp = self._read_resp(timeout = min(remaining, 1.0))

            if resp is None:
                if not self._ensure_subprocess_alive():
                    raise RuntimeError(
                        "Inference subprocess crashed during audio generation"
                    )
                continue

            rtype = resp.get("type", "")

            if rtype == "audio_done":
                wav_bytes = base64.b64decode(resp["wav_base64"])
                sample_rate = resp["sample_rate"]
                return wav_bytes, sample_rate

            if rtype == "audio_error":
                raise RuntimeError(resp.get("error", "Audio generation failed"))

            if rtype == "error":
                raise RuntimeError(resp.get("error", "Unknown error"))

            if rtype == "status":
                continue

        raise RuntimeError("Timeout waiting for audio generation (120s)")