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