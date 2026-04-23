def get_models(self, *, force_refresh: bool = False) -> dict[str, dict[str, Any]]:
        """Get available models with their capabilities.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary mapping model IDs to their metadata:
            {
                "model-id": {
                    "name": "model-id",
                    "provider": "Provider Name",
                    "tool_calling": True/False,
                    "preview": True/False,
                    "not_supported": True/False,  # for non-LLM models
                    "last_tested": "2025-01-06T10:30:00"
                }
            }
        """
        # Try to load from cache first
        if not force_refresh:
            cached = self._load_cache()
            if cached:
                logger.info("Using cached Groq model metadata")
                return cached

        # Fetch fresh data from API
        if not self.api_key:
            logger.warning("No API key provided, using minimal fallback list")
            return self._get_fallback_models()

        try:
            models_metadata = {}

            # Step 1: Get list of available models
            available_models = self._fetch_available_models()
            logger.info(f"Found {len(available_models)} models from Groq API")

            # Step 2: Categorize models
            llm_models = []
            non_llm_models = []

            for model_id in available_models:
                if any(pattern in model_id.lower() for pattern in self.SKIP_PATTERNS):
                    non_llm_models.append(model_id)
                else:
                    llm_models.append(model_id)

            # Step 3: Test LLM models for chat completion and tool calling
            logger.info(f"Testing {len(llm_models)} LLM models for capabilities...")
            for model_id in llm_models:
                supports_chat = self._test_chat_completion(model_id)
                if supports_chat is False:
                    # Model doesn't support chat completions at all (e.g. speech models)
                    non_llm_models.append(model_id)
                    logger.debug(f"{model_id}: does not support chat completions, skipping")
                    continue
                if supports_chat is None:
                    # Transient/access error - assume chat is supported (benefit of the doubt)
                    logger.info(f"{model_id}: chat test indeterminate, assuming chat supported")
                supports_tools = self._test_tool_calling(model_id)
                if supports_tools is None:
                    # Transient/access error on tool test - skip to avoid caching a false negative
                    logger.info(f"{model_id}: tool test indeterminate, skipping (will retry next refresh)")
                    continue
                models_metadata[model_id] = {
                    "name": model_id,
                    "provider": self._get_provider_name(model_id),
                    "tool_calling": supports_tools,
                    "preview": "preview" in model_id.lower() or "/" in model_id,
                    "last_tested": datetime.now(timezone.utc).isoformat(),
                }
                logger.debug(f"{model_id}: tool_calling={supports_tools}")

            # Step 4: Add non-LLM models as unsupported
            for model_id in non_llm_models:
                models_metadata[model_id] = {
                    "name": model_id,
                    "provider": self._get_provider_name(model_id),
                    "not_supported": True,
                    "last_tested": datetime.now(timezone.utc).isoformat(),
                }

            # Save to cache
            self._save_cache(models_metadata)

        except (requests.RequestException, KeyError, ValueError, ImportError):
            logger.exception("Error discovering models")
            return self._get_fallback_models()
        else:
            return models_metadata