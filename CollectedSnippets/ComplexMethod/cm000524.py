async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        logger.debug(f"Calling LLM with input data: {input_data}")
        prompt = [json.to_dict(p) for p in input_data.conversation_history or [] if p]

        values = input_data.prompt_values
        if values:
            input_data.prompt = await fmt.format_string(input_data.prompt, values)
            input_data.sys_prompt = await fmt.format_string(
                input_data.sys_prompt, values
            )

        if input_data.sys_prompt:
            prompt.append({"role": "system", "content": input_data.sys_prompt})

        # Use a one-time unique tag to prevent collisions with user/LLM content
        output_tag_id = self.get_collision_proof_output_tag_id()
        output_tag_start = f'<json_output id="{output_tag_id}">'
        if input_data.expected_format:
            sys_prompt = self.response_format_instructions(
                input_data.expected_format,
                list_mode=input_data.list_result,
                pure_json_mode=input_data.force_json_output,
                output_tag_start=output_tag_start,
            )
            prompt.append({"role": "system", "content": sys_prompt})

        if input_data.prompt:
            prompt.append({"role": "user", "content": input_data.prompt})

        def validate_response(parsed: object) -> str | None:
            try:
                if not isinstance(parsed, dict):
                    return f"Expected a dictionary, but got {type(parsed)}"
                miss_keys = set(input_data.expected_format.keys()) - set(parsed.keys())
                if miss_keys:
                    return f"Missing keys: {miss_keys}"
                return None
            except JSONDecodeError as e:
                return f"JSON decode error: {e}"

        error_feedback_message = ""
        llm_model = input_data.model
        total_provider_cost: float | None = None

        for retry_count in range(input_data.retry):
            logger.debug(f"LLM request: {prompt}")
            try:
                llm_response = await self.llm_call(
                    credentials=credentials,
                    llm_model=llm_model,
                    prompt=prompt,
                    compress_prompt_to_fit=input_data.compress_prompt_to_fit,
                    force_json_output=(
                        input_data.force_json_output
                        and bool(input_data.expected_format)
                    ),
                    ollama_host=input_data.ollama_host,
                    max_tokens=input_data.max_tokens,
                )
                response_text = llm_response.response
                # Accumulate token counts and provider_cost for every attempt
                # (each call costs tokens and USD, regardless of validation outcome).
                token_stats = NodeExecutionStats(
                    input_token_count=llm_response.prompt_tokens,
                    output_token_count=llm_response.completion_tokens,
                    cache_read_token_count=llm_response.cache_read_tokens,
                    cache_creation_token_count=llm_response.cache_creation_tokens,
                )
                self.merge_stats(token_stats)
                if llm_response.provider_cost is not None:
                    total_provider_cost = (
                        total_provider_cost or 0.0
                    ) + llm_response.provider_cost
                logger.debug(f"LLM attempt-{retry_count} response: {response_text}")

                if input_data.expected_format:
                    try:
                        response_obj = self.get_json_from_response(
                            response_text,
                            pure_json_mode=input_data.force_json_output,
                            output_tag_start=output_tag_start,
                        )
                    except (ValueError, JSONDecodeError) as parse_error:
                        censored_response = re.sub(r"[A-Za-z0-9]", "*", response_text)
                        response_snippet = (
                            f"{censored_response[:50]}...{censored_response[-30:]}"
                        )
                        logger.warning(
                            f"Error getting JSON from LLM response: {parse_error}\n\n"
                            f"Response start+end: `{response_snippet}`"
                        )
                        prompt.append({"role": "assistant", "content": response_text})

                        error_feedback_message = self.invalid_response_feedback(
                            parse_error,
                            was_parseable=False,
                            list_mode=input_data.list_result,
                            pure_json_mode=input_data.force_json_output,
                            output_tag_start=output_tag_start,
                        )
                        prompt.append(
                            {"role": "user", "content": error_feedback_message}
                        )
                        continue

                    # Handle object response for `force_json_output`+`list_result`
                    if input_data.list_result and isinstance(response_obj, dict):
                        if "results" in response_obj and isinstance(
                            response_obj["results"], list
                        ):
                            response_obj = response_obj["results"]
                        else:
                            error_feedback_message = (
                                "Expected an array of objects in the 'results' key, "
                                f"but got: {response_obj}"
                            )
                            prompt.append(
                                {"role": "assistant", "content": response_text}
                            )
                            prompt.append(
                                {"role": "user", "content": error_feedback_message}
                            )
                            continue

                    validation_errors = "\n".join(
                        [
                            validation_error
                            for response_item in (
                                response_obj
                                if isinstance(response_obj, list)
                                else [response_obj]
                            )
                            if (validation_error := validate_response(response_item))
                        ]
                    )

                    if not validation_errors:
                        self.merge_stats(
                            NodeExecutionStats(
                                llm_call_count=retry_count + 1,
                                llm_retry_count=retry_count,
                                provider_cost=total_provider_cost,
                            )
                        )
                        yield "response", response_obj
                        yield "prompt", self.prompt
                        return

                    prompt.append({"role": "assistant", "content": response_text})
                    error_feedback_message = self.invalid_response_feedback(
                        validation_errors,
                        was_parseable=True,
                        list_mode=input_data.list_result,
                        pure_json_mode=input_data.force_json_output,
                        output_tag_start=output_tag_start,
                    )
                    prompt.append({"role": "user", "content": error_feedback_message})
                else:
                    self.merge_stats(
                        NodeExecutionStats(
                            llm_call_count=retry_count + 1,
                            llm_retry_count=retry_count,
                            provider_cost=total_provider_cost,
                        )
                    )
                    yield "response", {"response": response_text}
                    yield "prompt", self.prompt
                    return
            except Exception as e:
                is_user_error = (
                    isinstance(e, (anthropic.APIStatusError, openai.APIStatusError))
                    and e.status_code in USER_ERROR_STATUS_CODES
                )
                if is_user_error:
                    logger.warning(f"Error calling LLM: {e}")
                    error_feedback_message = f"Error calling LLM: {e}"
                    break
                else:
                    logger.exception(f"Error calling LLM: {e}")
                if (
                    "maximum context length" in str(e).lower()
                    or "token limit" in str(e).lower()
                ):
                    if input_data.max_tokens is None:
                        input_data.max_tokens = llm_model.max_output_tokens or 4096
                    input_data.max_tokens = int(input_data.max_tokens * 0.85)
                    logger.debug(
                        f"Reducing max_tokens to {input_data.max_tokens} for next attempt"
                    )
                    # Don't add retry prompt for token limit errors,
                    # just retry with lower maximum output tokens

                error_feedback_message = f"Error calling LLM: {e}"

        # All retries exhausted or user-error break: persist accumulated cost so
        # the executor can still charge/report the spend even on failure.
        if total_provider_cost is not None:
            self.merge_stats(NodeExecutionStats(provider_cost=total_provider_cost))
        raise RuntimeError(error_feedback_message)