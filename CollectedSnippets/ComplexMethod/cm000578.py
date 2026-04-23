async def call_perplexity(
        self,
        credentials: APIKeyCredentials,
        model: PerplexityModel,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Call Perplexity via OpenRouter and extract annotations."""
        client = openai.AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=credentials.api_key.get_secret_value(),
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://agpt.co",
                    "X-Title": "AutoGPT",
                },
                model=model.value,
                messages=messages,
                max_tokens=max_tokens,
            )

            if not response.choices:
                raise ValueError("No response from Perplexity via OpenRouter.")

            # Extract the response content
            response_content = response.choices[0].message.content or ""

            # Extract annotations if present in the message
            annotations = []
            if hasattr(response.choices[0].message, "annotations"):
                # If annotations are directly available
                annotations = response.choices[0].message.annotations
            else:
                # Check if there's a raw response with annotations
                raw = getattr(response.choices[0].message, "_raw_response", None)
                if isinstance(raw, dict) and "annotations" in raw:
                    annotations = raw["annotations"]

            if not annotations and hasattr(response, "model_extra"):
                # Check model_extra for annotations
                model_extra = response.model_extra
                if isinstance(model_extra, dict):
                    # Check in choices
                    if "choices" in model_extra and len(model_extra["choices"]) > 0:
                        choice = model_extra["choices"][0]
                        if "message" in choice and "annotations" in choice["message"]:
                            annotations = choice["message"]["annotations"]

            # Also check the raw response object for annotations
            if not annotations:
                raw = getattr(response, "_raw_response", None)
                if isinstance(raw, dict):
                    # Check various possible locations for annotations
                    if "annotations" in raw:
                        annotations = raw["annotations"]
                    elif "choices" in raw and len(raw["choices"]) > 0:
                        choice = raw["choices"][0]
                        if "message" in choice and "annotations" in choice["message"]:
                            annotations = choice["message"]["annotations"]

            # Update execution stats. ``execution_stats`` is instance state,
            # so always reset token counters — a response without ``usage``
            # must not leak a previous run's tokens into ``PlatformCostLog``.
            self.execution_stats.input_token_count = 0
            self.execution_stats.output_token_count = 0
            if response.usage:
                self.execution_stats.input_token_count = response.usage.prompt_tokens
                self.execution_stats.output_token_count = (
                    response.usage.completion_tokens
                )
            # OpenRouter's ``x-total-cost`` response header carries the real
            # per-request USD cost. Piping it into ``provider_cost`` lets the
            # direct-run ``PlatformCostLog`` flow
            # (``executor.cost_tracking::log_system_credential_cost``) record
            # the actual operator-side spend instead of inferring from tokens.
            # Always overwrite — ``execution_stats`` is instance state, so a
            # response without the header must not reuse a previous run's cost.
            self.execution_stats.provider_cost = extract_openrouter_cost(response)

            return {"response": response_content, "annotations": annotations or []}

        except Exception as e:
            logger.error(f"Error calling Perplexity: {e}")
            raise