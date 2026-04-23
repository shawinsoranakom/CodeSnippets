def chat_streamly(self, system, history, gen_conf={}, **kwargs):
        if "claude" in self.model_name:
            if "max_tokens" in gen_conf:
                del gen_conf["max_tokens"]
            ans = ""
            total_tokens = 0
            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    messages=history,
                    system=system,
                    stream=True,
                    **gen_conf,
                )
                for res in response.iter_lines():
                    res = res.decode("utf-8")
                    if "content_block_delta" in res and "data" in res:
                        text = json.loads(res[6:])["delta"]["text"]
                        ans = text
                        total_tokens += num_tokens_from_string(text)
            except Exception as e:
                yield ans + "\n**ERROR**: " + str(e)

            yield total_tokens
        else:
            # Gemini models with google-genai SDK
            ans = ""
            total_tokens = 0

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
                # google-genai uses 'model' instead of 'assistant'
                role = "model" if item["role"] == "assistant" else item["role"]
                content = Content(
                    role=role,
                    parts=[Part(text=item["content"])],
                )
                contents.append(content)

            try:
                for chunk in self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                ):
                    text = chunk.text
                    ans = text
                    total_tokens += num_tokens_from_string(text)
                    yield ans

            except Exception as e:
                yield ans + "\n**ERROR**: " + str(e)

            yield total_tokens