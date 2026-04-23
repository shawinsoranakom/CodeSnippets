def _chat(self, history, gen_conf={}, **kwargs):
        system = history[0]["content"] if history and history[0]["role"] == "system" else ""

        if "claude" in self.model_name:
            gen_conf = self._clean_conf(gen_conf)
            response = self.client.messages.create(
                model=self.model_name,
                messages=[h for h in history if h["role"] != "system"],
                system=system,
                stream=False,
                **gen_conf,
            ).json()
            ans = response["content"][0]["text"]
            if response["stop_reason"] == "max_tokens":
                ans += "...\nFor the content length reason, it stopped, continue?" if is_english([ans]) else "······\n由于长度的原因，回答被截断了，要继续吗？"
            return (
                ans,
                response["usage"]["input_tokens"] + response["usage"]["output_tokens"],
            )

        # Gemini models with google-genai SDK
        # Set default thinking_budget=0 if not specified
        if "thinking_budget" not in gen_conf:
            gen_conf["thinking_budget"] = 0

        thinking_budget = gen_conf.pop("thinking_budget", 0)
        gen_conf = self._clean_conf(gen_conf)

        # Build GenerateContentConfig
        try:
            from google.genai.types import Content, GenerateContentConfig, Part, ThinkingConfig
        except ImportError as e:
            logging.error(f"[GoogleChat] Failed to import google-genai: {e}. Please install: pip install google-genai>=1.41.0")
            raise

        config_dict = {}
        if system:
            config_dict["system_instruction"] = system
        if "temperature" in gen_conf:
            config_dict["temperature"] = gen_conf["temperature"]
        if "top_p" in gen_conf:
            config_dict["top_p"] = gen_conf["top_p"]
        if "max_output_tokens" in gen_conf:
            config_dict["max_output_tokens"] = gen_conf["max_output_tokens"]

        # Add ThinkingConfig
        config_dict["thinking_config"] = ThinkingConfig(thinking_budget=thinking_budget)

        config = GenerateContentConfig(**config_dict)

        # Convert history to google-genai Content format
        contents = []
        for item in history:
            if item["role"] == "system":
                continue
            # google-genai uses 'model' instead of 'assistant'
            role = "model" if item["role"] == "assistant" else item["role"]
            content = Content(
                role=role,
                parts=[Part(text=item["content"])],
            )
            contents.append(content)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )

        ans = response.text
        # Get token count from response
        try:
            total_tokens = response.usage_metadata.total_token_count
        except Exception:
            total_tokens = 0

        return ans, total_tokens