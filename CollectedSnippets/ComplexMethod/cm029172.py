async def ainvoke(
		self,
		messages: list[BaseMessage],
		output_format: type[T] | None = None,
		**kwargs: Any,
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		from litellm import acompletion  # type: ignore[reportMissingImports]
		from litellm.exceptions import APIConnectionError, APIError, RateLimitError, Timeout  # type: ignore[reportMissingImports]
		from litellm.types.utils import ModelResponse  # type: ignore[reportMissingImports]

		litellm_messages = LiteLLMMessageSerializer.serialize(messages)

		params: dict[str, Any] = {
			'model': self.model,
			'messages': litellm_messages,
			'num_retries': self.max_retries,
		}

		if self.temperature is not None:
			params['temperature'] = self.temperature
		if self.max_tokens is not None:
			params['max_tokens'] = self.max_tokens
		if self.api_key:
			params['api_key'] = self.api_key
		if self.api_base:
			params['api_base'] = self.api_base
		if self.metadata:
			params['metadata'] = self.metadata

		if output_format is not None:
			schema = SchemaOptimizer.create_optimized_json_schema(output_format)
			params['response_format'] = {
				'type': 'json_schema',
				'json_schema': {
					'name': 'agent_output',
					'strict': True,
					'schema': schema,
				},
			}

		try:
			raw_response = await acompletion(**params)
		except RateLimitError as e:
			raise ModelRateLimitError(
				message=str(e),
				model=self.name,
			) from e
		except Timeout as e:
			raise ModelProviderError(
				message=f'Request timed out: {e}',
				model=self.name,
			) from e
		except APIConnectionError as e:
			raise ModelProviderError(
				message=str(e),
				model=self.name,
			) from e
		except APIError as e:
			status = getattr(e, 'status_code', 502) or 502
			raise ModelProviderError(
				message=str(e),
				status_code=status,
				model=self.name,
			) from e
		except ModelProviderError:
			raise
		except Exception as e:
			raise ModelProviderError(
				message=str(e),
				model=self.name,
			) from e

		assert isinstance(raw_response, ModelResponse), f'Expected ModelResponse, got {type(raw_response)}'
		response: ModelResponse = raw_response

		choice = response.choices[0] if response.choices else None
		if choice is None:
			raise ModelProviderError(
				message='Empty response: no choices returned by the model',
				status_code=502,
				model=self.name,
			)

		content = choice.message.content or ''
		usage = self._parse_usage(response)
		stop_reason = choice.finish_reason

		thinking: str | None = None
		msg_obj = choice.message
		reasoning = getattr(msg_obj, 'reasoning_content', None)
		if reasoning:
			thinking = str(reasoning)

		if output_format is not None:
			if not content:
				raise ModelProviderError(
					message='Model returned empty content for structured output request',
					status_code=500,
					model=self.name,
				)
			parsed = output_format.model_validate_json(content)
			return ChatInvokeCompletion(
				completion=parsed,
				thinking=thinking,
				usage=usage,
				stop_reason=stop_reason,
			)

		return ChatInvokeCompletion(
			completion=content,
			thinking=thinking,
			usage=usage,
			stop_reason=stop_reason,
		)