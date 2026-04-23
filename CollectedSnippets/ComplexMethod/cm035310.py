def init_model_info(self) -> None:
        if self._tried_model_info:
            return
        self._tried_model_info = True
        try:
            if self.config.model.startswith('openrouter'):
                self.model_info = litellm.get_model_info(self.config.model)
        except Exception as e:
            logger.debug(f'Error getting model info: {e}')

        if self.config.model.startswith('litellm_proxy/'):
            # IF we are using LiteLLM proxy, get model info from LiteLLM proxy
            # GET {base_url}/v1/model/info with litellm_model_id as path param
            base_url = self.config.base_url.strip() if self.config.base_url else ''
            if not base_url.startswith(('http://', 'https://')):
                base_url = 'http://' + base_url

            response = httpx.get(
                f'{base_url}/v1/model/info',
                headers={
                    'Authorization': f'Bearer {self.config.api_key.get_secret_value() if self.config.api_key else None}'
                },
            )

            try:
                resp_json = response.json()
                if 'data' not in resp_json:
                    logger.info(
                        f'No data field in model info response from LiteLLM proxy: {resp_json}'
                    )
                all_model_info = resp_json.get('data', [])
            except Exception as e:
                logger.info(f'Error parsing JSON response from LiteLLM proxy: {e}')
                all_model_info = []
            current_model_info = next(
                (
                    info
                    for info in all_model_info
                    if info['model_name']
                    == self.config.model.removeprefix('litellm_proxy/')
                ),
                None,
            )
            if current_model_info:
                self.model_info = current_model_info['model_info']
                logger.debug(f'Got model info from litellm proxy: {self.model_info}')

        # Last two attempts to get model info from NAME
        if not self.model_info:
            try:
                self.model_info = litellm.get_model_info(
                    self.config.model.split(':')[0]
                )
            # noinspection PyBroadException
            except Exception:
                pass
        if not self.model_info:
            try:
                self.model_info = litellm.get_model_info(
                    self.config.model.split('/')[-1]
                )
            # noinspection PyBroadException
            except Exception:
                pass
        from openhands.io import json

        logger.debug(
            f'Model info: {json.dumps({"model": self.config.model, "base_url": self.config.base_url}, indent=2)}'
        )

        if self.config.model.startswith('huggingface'):
            # HF doesn't support the OpenAI default value for top_p (1)
            logger.debug(
                f'Setting top_p to 0.9 for Hugging Face model: {self.config.model}'
            )
            self.config.top_p = 0.9 if self.config.top_p == 1 else self.config.top_p

        # Set max_input_tokens from model info if not explicitly set
        if (
            self.config.max_input_tokens is None
            and self.model_info is not None
            and 'max_input_tokens' in self.model_info
            and isinstance(self.model_info['max_input_tokens'], int)
        ):
            self.config.max_input_tokens = self.model_info['max_input_tokens']

        # Set max_output_tokens from model info if not explicitly set
        if self.config.max_output_tokens is None:
            # Special case for Claude Sonnet models
            sonnet_models = [
                'claude-3-7-sonnet',
                'claude-3.7-sonnet',
                'claude-sonnet-4',
                'claude-sonnet-4-5-20250929',
                'claude-haiku-4-5-20251001',
            ]
            if any(model in self.config.model for model in sonnet_models):
                self.config.max_output_tokens = 64000  # litellm set max to 128k, but that requires a header to be set
            # Try to get from model info
            elif self.model_info is not None:
                # max_output_tokens has precedence over max_tokens
                if 'max_output_tokens' in self.model_info and isinstance(
                    self.model_info['max_output_tokens'], int
                ):
                    self.config.max_output_tokens = self.model_info['max_output_tokens']
                elif 'max_tokens' in self.model_info and isinstance(
                    self.model_info['max_tokens'], int
                ):
                    self.config.max_output_tokens = self.model_info['max_tokens']

        # Initialize function calling using centralized model features
        features = get_features(self.config.model)
        if self.config.native_tool_calling is None:
            self._function_calling_active = features.supports_function_calling
        else:
            self._function_calling_active = self.config.native_tool_calling