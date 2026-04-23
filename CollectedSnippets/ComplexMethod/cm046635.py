def generate_audio_response(
        self,
        text: str,
        audio_type: str,
        temperature: float = 0.6,
        top_p: float = 0.95,
        top_k: int = 50,
        min_p: float = 0.0,
        max_new_tokens: int = 2048,
        repetition_penalty: float = 1.1,
    ) -> tuple:
        """
        Generate TTS audio via llama-server /completion + codec decoding.
        Returns (wav_bytes, sample_rate).
        """
        if audio_type not in self._TTS_PROMPTS:
            raise RuntimeError(f"GGUF TTS does not support '{audio_type}' codec.")

        tpl, stop, need_ids = self._TTS_PROMPTS[audio_type]

        payload: dict = {
            "prompt": tpl.format(text = text),
            "stream": False,
            "n_predict": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k if top_k >= 0 else 0,
            "min_p": min_p,
            "repeat_penalty": repetition_penalty,
        }
        if stop:
            payload["stop"] = stop
        if need_ids:
            payload["n_probs"] = 1

        _auth_headers = (
            {"Authorization": f"Bearer {self._api_key}"} if self._api_key else None
        )
        with httpx.Client(
            timeout = httpx.Timeout(300, connect = 10), headers = _auth_headers
        ) as client:
            resp = client.post(f"{self.base_url}/completion", json = payload)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"llama-server returned {resp.status_code}: {resp.text}"
                )

        data = resp.json()
        token_ids = (
            [p["id"] for p in data.get("completion_probabilities", []) if "id" in p]
            if need_ids
            else None
        )

        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        return LlamaCppBackend._codec_mgr.decode(
            audio_type, device, token_ids = token_ids, text = data.get("content", "")
        )