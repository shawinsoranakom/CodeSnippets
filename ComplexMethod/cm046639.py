def _fetch_top_models(self) -> None:
        """Fetch top GGUF and non-GGUF repos from unsloth by downloads."""
        try:
            import httpx

            resp = httpx.get(
                "https://huggingface.co/api/models",
                params = {
                    "author": "unsloth",
                    "sort": "downloads",
                    "direction": "-1",
                    "limit": "80",
                },
                timeout = 15,
            )
            if resp.status_code == 200:
                models = resp.json()
                # Top 40 GGUFs - frontend pages through them on-demand via
                # infinite scroll, so we send a deep pool.
                gguf_ids = [
                    m["id"] for m in models if m.get("id", "").upper().endswith("-GGUF")
                ][:40]
                # Top 40 non-GGUF hub models
                hub_ids = [
                    m["id"]
                    for m in models
                    if not m.get("id", "").upper().endswith("-GGUF")
                ][:40]
                if gguf_ids:
                    self._top_gguf_cache = gguf_ids
                    logger.info("Top GGUF models: %s", gguf_ids)
                if hub_ids:
                    self._top_hub_cache = hub_ids
                    logger.info("Top hub models: %s", hub_ids)
        except Exception as e:
            logger.warning("Failed to fetch top models: %s", e)
        finally:
            self._top_models_ready.set()