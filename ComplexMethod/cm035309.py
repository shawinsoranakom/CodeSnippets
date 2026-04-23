def __init__(
        self,
        config: LLMConfig,
        service_id: str,
        metrics: Metrics | None = None,
        retry_listener: Callable[[int, int], None] | None = None,
    ) -> None:
        """Initializes the LLM. If LLMConfig is passed, its values will be the fallback.

        Passing simple parameters always overrides config.

        Args:
            config: The LLM configuration.
            metrics: The metrics to use.
        """
        self._tried_model_info = False
        self.cost_metric_supported: bool = True
        self.config: LLMConfig = copy.deepcopy(config)
        self.service_id = service_id
        self.metrics: Metrics = (
            metrics if metrics is not None else Metrics(model_name=config.model)
        )

        self.model_info: ModelInfo | None = None
        self._function_calling_active: bool = False
        self.retry_listener = retry_listener
        if self.config.log_completions:
            if self.config.log_completions_folder is None:
                raise RuntimeError(
                    'log_completions_folder is required when log_completions is enabled'
                )
            os.makedirs(self.config.log_completions_folder, exist_ok=True)

        # call init_model_info to initialize config.max_output_tokens
        # which is used in partial function
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.init_model_info()
        if self.vision_is_active():
            logger.debug('LLM: model has vision enabled')
        if self.is_caching_prompt_active():
            logger.debug('LLM: caching prompt enabled')
        if self.is_function_calling_active():
            logger.debug('LLM: model supports function calling')

        # if using a custom tokenizer, make sure it's loaded and accessible in the format expected by litellm
        if self.config.custom_tokenizer is not None:
            self.tokenizer = create_pretrained_tokenizer(self.config.custom_tokenizer)
        else:
            self.tokenizer = None

        # set up the completion function
        kwargs: dict[str, Any] = {
            'temperature': self.config.temperature,
            'max_completion_tokens': self.config.max_output_tokens,
        }
        if self.config.top_k is not None:
            # openai doesn't expose top_k
            # litellm will handle it a bit differently than the openai-compatible params
            kwargs['top_k'] = self.config.top_k
        if self.config.top_p is not None:
            # openai doesn't expose top_p, but litellm does
            kwargs['top_p'] = self.config.top_p

        # Handle OpenHands provider - rewrite to litellm_proxy
        if self.config.model.startswith('openhands/'):
            model_name = self.config.model.removeprefix('openhands/')
            self.config.model = f'litellm_proxy/{model_name}'
            self.config.base_url = _get_openhands_llm_base_url()
            logger.debug(
                f'Rewrote openhands/{model_name} to {self.config.model} with base URL {self.config.base_url}'
            )

        features = get_features(self.config.model)
        if features.supports_reasoning_effort:
            # For Gemini models, only map 'low' to optimized thinking budget
            # Let other reasoning_effort values pass through to API as-is
            if 'gemini-2.5-pro' in self.config.model:
                logger.debug(
                    f'Gemini model {self.config.model} with reasoning_effort {self.config.reasoning_effort}'
                )
                if self.config.reasoning_effort in {None, 'low', 'none'}:
                    kwargs['thinking'] = {'budget_tokens': 128}
                    kwargs['allowed_openai_params'] = ['thinking']
                    kwargs.pop('reasoning_effort', None)
                else:
                    kwargs['reasoning_effort'] = self.config.reasoning_effort
                logger.debug(
                    f'Gemini model {self.config.model} with reasoning_effort {self.config.reasoning_effort} mapped to thinking {kwargs.get("thinking")}'
                )
            elif any(
                k in self.config.model
                for k in (
                    'claude-sonnet-4-5',
                    'claude-haiku-4-5-20251001',
                    'claude-opus-4-6',
                )
            ):
                # don't send reasoning_effort to specific Claude Sonnet/Haiku 4.5 variants or Claude Opus 4.6
                kwargs.pop('reasoning_effort', None)
            else:
                if self.config.reasoning_effort is not None:
                    kwargs['reasoning_effort'] = self.config.reasoning_effort
            kwargs.pop(
                'temperature'
            )  # temperature is not supported for reasoning models
            kwargs.pop('top_p')  # reasoning model like o3 doesn't support top_p
        # Azure issue: https://github.com/OpenHands/OpenHands/issues/6777
        if self.config.model.startswith('azure'):
            kwargs['max_tokens'] = self.config.max_output_tokens
            kwargs.pop('max_completion_tokens')

        # Add safety settings for models that support them
        if 'mistral' in self.config.model.lower() and self.config.safety_settings:
            kwargs['safety_settings'] = self.config.safety_settings
        elif 'gemini' in self.config.model.lower() and self.config.safety_settings:
            kwargs['safety_settings'] = self.config.safety_settings

        # support AWS Bedrock provider
        kwargs['aws_region_name'] = self.config.aws_region_name
        if self.config.aws_access_key_id:
            kwargs['aws_access_key_id'] = (
                self.config.aws_access_key_id.get_secret_value()
            )
        if self.config.aws_secret_access_key:
            kwargs['aws_secret_access_key'] = (
                self.config.aws_secret_access_key.get_secret_value()
            )

        # Explicitly disable Anthropic extended thinking for Opus 4.1 to avoid
        # requiring 'thinking' content blocks. See issue #10510.
        if 'claude-opus-4-1' in self.config.model.lower():
            kwargs['thinking'] = {'type': 'disabled'}

        # Anthropic constraint: Opus 4.1, Opus 4.5, Opus 4.6, and Sonnet 4.x models cannot accept both temperature and top_p
        # Prefer temperature (drop top_p) if both are specified.
        _model_lower = self.config.model.lower()
        # Apply to Opus 4.1, Opus 4.5, Opus 4.6, and Sonnet 4.x models to avoid API errors
        if (
            ('claude-opus-4-1' in _model_lower)
            or ('claude-opus-4-5' in _model_lower)
            or ('claude-opus-4-6' in _model_lower)
            or ('claude-sonnet-4' in _model_lower)
        ) and ('temperature' in kwargs and 'top_p' in kwargs):
            kwargs.pop('top_p', None)

        # Add completion_kwargs if present
        if self.config.completion_kwargs is not None:
            kwargs.update(self.config.completion_kwargs)

        self._completion = partial(
            litellm_completion,
            model=self.config.model,
            api_key=self.config.api_key.get_secret_value()
            if self.config.api_key
            else None,
            base_url=self.config.base_url,
            api_version=self.config.api_version,
            custom_llm_provider=self.config.custom_llm_provider,
            timeout=self.config.timeout,
            drop_params=self.config.drop_params,
            seed=self.config.seed,
            **kwargs,
        )

        self._completion_unwrapped = self._completion

        @self.retry_decorator(
            num_retries=self.config.num_retries,
            retry_exceptions=LLM_RETRY_EXCEPTIONS,
            retry_min_wait=self.config.retry_min_wait,
            retry_max_wait=self.config.retry_max_wait,
            retry_multiplier=self.config.retry_multiplier,
            retry_listener=self.retry_listener,
        )
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for the litellm completion function. Logs the input and output of the completion function."""
            from openhands.io import json

            messages_kwarg: (
                dict[str, Any] | Message | list[dict[str, Any]] | list[Message]
            ) = []
            mock_function_calling = not self.is_function_calling_active()

            # some callers might send the model and messages directly
            # litellm allows positional args, like completion(model, messages, **kwargs)
            if len(args) > 1:
                # ignore the first argument if it's provided (it would be the model)
                # design wise: we don't allow overriding the configured values
                # implementation wise: the partial function set the model as a kwarg already
                # as well as other kwargs
                messages_kwarg = args[1] if len(args) > 1 else args[0]
                kwargs['messages'] = messages_kwarg

                # remove the first args, they're sent in kwargs
                args = args[2:]
            elif 'messages' in kwargs:
                messages_kwarg = kwargs['messages']

            # ensure we work with a list of messages
            messages_list = (
                messages_kwarg if isinstance(messages_kwarg, list) else [messages_kwarg]
            )
            # Format Message objects to dict format if needed
            messages: list[dict] = []
            if messages_list and isinstance(messages_list[0], Message):
                messages = self.format_messages_for_llm(
                    cast(list[Message], messages_list)
                )
            else:
                messages = cast(list[dict[str, Any]], messages_list)

            kwargs['messages'] = messages

            # handle conversion of to non-function calling messages if needed
            original_fncall_messages = copy.deepcopy(messages)
            mock_fncall_tools = None
            # if the agent or caller has defined tools, and we mock via prompting, convert the messages
            if mock_function_calling and 'tools' in kwargs:
                add_in_context_learning_example = True
                if (
                    'openhands-lm' in self.config.model
                    or 'devstral' in self.config.model
                ):
                    add_in_context_learning_example = False

                messages = convert_fncall_messages_to_non_fncall_messages(
                    messages,
                    kwargs['tools'],
                    add_in_context_learning_example=add_in_context_learning_example,
                )
                kwargs['messages'] = messages

                # add stop words if the model supports it and stop words are not disabled
                if (
                    get_features(self.config.model).supports_stop_words
                    and not self.config.disable_stop_word
                ):
                    kwargs['stop'] = STOP_WORDS

                mock_fncall_tools = kwargs.pop('tools')
                if 'openhands-lm' in self.config.model:
                    # If we don't have this, we might run into issue when serving openhands-lm
                    # using SGLang
                    # BadRequestError: litellm.BadRequestError: OpenAIException - Error code: 400 - {'object': 'error', 'message': '400', 'type': 'Failed to parse fc related info to json format!', 'param': None, 'code': 400}
                    kwargs['tool_choice'] = 'none'
                else:
                    # tool_choice should not be specified when mocking function calling
                    kwargs.pop('tool_choice', None)

            # if we have no messages, something went very wrong
            if not messages:
                raise ValueError(
                    'The messages list is empty. At least one message is required.'
                )

            # log the entire LLM prompt
            self.log_prompt(messages)

            # set litellm modify_params to the configured value
            # True by default to allow litellm to do transformations like adding a default message, when a message is empty
            # NOTE: this setting is global; unlike drop_params, it cannot be overridden in the litellm completion partial
            litellm.modify_params = self.config.modify_params

            # if we're not using litellm proxy, remove the extra_body
            if 'litellm_proxy' not in self.config.model:
                kwargs.pop('extra_body', None)

            # Record start time for latency measurement
            start_time = time.time()
            # we don't support streaming here, thus we get a ModelResponse

            # Suppress httpx deprecation warnings during LiteLLM calls
            # This prevents the "Use 'content=<...>' to upload raw bytes/text content" warning
            # that appears when LiteLLM makes HTTP requests to LLM providers
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    'ignore', category=DeprecationWarning, module='httpx.*'
                )
                warnings.filterwarnings(
                    'ignore',
                    message=r'.*content=.*upload.*',
                    category=DeprecationWarning,
                )
                resp: ModelResponse = self._completion_unwrapped(*args, **kwargs)

            # Calculate and record latency
            latency = time.time() - start_time
            response_id = resp.get('id', 'unknown')
            self.metrics.add_response_latency(latency, response_id)

            non_fncall_response = copy.deepcopy(resp)

            # if we mocked function calling, and we have tools, convert the response back to function calling format
            if mock_function_calling and mock_fncall_tools is not None:
                if len(resp.choices) < 1:
                    raise LLMNoResponseError(
                        'Response choices is less than 1 - This is only seen in Gemini models so far. Response: '
                        + str(resp)
                    )

                non_fncall_response_message = resp.choices[0].message
                # messages is already a list with proper typing from line 223
                fn_call_messages_with_response = (
                    convert_non_fncall_messages_to_fncall_messages(
                        messages + [non_fncall_response_message], mock_fncall_tools
                    )
                )
                fn_call_response_message = fn_call_messages_with_response[-1]
                if not isinstance(fn_call_response_message, LiteLLMMessage):
                    fn_call_response_message = LiteLLMMessage(
                        **fn_call_response_message
                    )
                resp.choices[0].message = fn_call_response_message

            # Check if resp has 'choices' key with at least one item
            if not resp.get('choices') or len(resp['choices']) < 1:
                raise LLMNoResponseError(
                    'Response choices is less than 1 - This is only seen in Gemini models so far. Response: '
                    + str(resp)
                )

            # log the LLM response
            self.log_response(resp)

            # post-process the response first to calculate cost
            cost = self._post_completion(resp)

            # log for evals or other scripts that need the raw completion
            if self.config.log_completions:
                assert self.config.log_completions_folder is not None
                log_file = os.path.join(
                    self.config.log_completions_folder,
                    f'{self.config.model.replace("/", "__")}-{time.time()}.json',
                )

                # set up the dict to be logged
                _d = {
                    'messages': messages,
                    'response': resp,
                    'args': args,
                    'kwargs': {
                        k: v
                        for k, v in kwargs.items()
                        if k not in ('messages', 'client')
                    },
                    'timestamp': time.time(),
                    'cost': cost,
                }

                # if non-native function calling, save messages/response separately
                if mock_function_calling:
                    # Overwrite response as non-fncall to be consistent with messages
                    _d['response'] = non_fncall_response

                    # Save fncall_messages/response separately
                    _d['fncall_messages'] = original_fncall_messages
                    _d['fncall_response'] = resp
                with open(log_file, 'w') as f:
                    f.write(json.dumps(_d))

            return resp

        self._completion = wrapper