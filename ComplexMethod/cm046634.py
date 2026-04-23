def detect_audio_type(self) -> Optional[str]:
        """Detect audio/TTS codec by probing the loaded model's vocabulary."""
        if not self.is_loaded:
            return None
        try:
            _auth_headers = (
                {"Authorization": f"Bearer {self._api_key}"} if self._api_key else None
            )
            with httpx.Client(timeout = 10, headers = _auth_headers) as client:

                def _detok(tid: int) -> str:
                    r = client.post(
                        f"{self.base_url}/detokenize", json = {"tokens": [tid]}
                    )
                    return r.json().get("content", "") if r.status_code == 200 else ""

                def _tok(text: str) -> list[int]:
                    r = client.post(
                        f"{self.base_url}/tokenize",
                        json = {"content": text, "add_special": False},
                    )
                    return r.json().get("tokens", []) if r.status_code == 200 else []

                # Check codec-specific tokens (not generic ones that may exist in non-audio models)
                if "<custom_token_" in _detok(128258) and "<custom_token_" in _detok(
                    128259
                ):
                    return "snac"
                if len(_tok("<|AUDIO|>")) == 1 and len(_tok("<|audio_eos|>")) == 1:
                    return "csm"
                if len(_tok("<|startoftranscript|>")) == 1:
                    return "whisper"
                if (
                    len(_tok("<|bicodec_semantic_0|>")) == 1
                    and len(_tok("<|bicodec_global_0|>")) == 1
                ):
                    return "bicodec"
                if len(_tok("<|c1_0|>")) == 1 and len(_tok("<|c2_0|>")) == 1:
                    return "dac"
        except Exception as e:
            logger.debug(f"Audio type detection failed: {e}")
        return None