async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None, **kwargs: Any
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		payload: dict[str, Any] = {
			'model': self.model,
			'messages': self._serialize_messages(messages),
		}

		# Generation params
		if self.temperature is not None:
			payload['temperature'] = self.temperature
		if self.top_p is not None:
			payload['top_p'] = self.top_p
		if self.max_tokens is not None:
			payload['max_tokens'] = self.max_tokens
		if self.seed is not None:
			payload['seed'] = self.seed
		if self.safe_prompt:
			payload['safe_prompt'] = self.safe_prompt

		# Structured output path
		if output_format is not None:
			payload['response_format'] = {
				'type': 'json_schema',
				'json_schema': {
					'name': 'agent_output',
					'strict': True,
					'schema': MistralSchemaOptimizer.create_mistral_compatible_schema(output_format),
				},
			}

		try:
			data = await self._post(payload)
			choices = data.get('choices', [])
			if not choices:
				raise ModelProviderError('Mistral returned no choices', model=self.name)

			content_text = self._extract_content_text(choices[0])
			usage = self._build_usage(data.get('usage'))

			if output_format is None:
				return ChatInvokeCompletion(completion=content_text, usage=usage)

			parsed = output_format.model_validate_json(content_text)
			return ChatInvokeCompletion(completion=parsed, usage=usage)

		except ModelRateLimitError:
			raise
		except ModelProviderError:
			raise
		except Exception as e:
			logger.error(f'Mistral invocation failed: {e}')
			raise ModelProviderError(message=str(e), model=self.name) from e