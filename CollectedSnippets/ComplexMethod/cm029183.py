async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None, **kwargs: Any
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		"""
		Invoke the model with the given messages through Vercel AI Gateway.

		Args:
		    messages: List of chat messages
		    output_format: Optional Pydantic model class for structured output

		Returns:
		    Either a string response or an instance of output_format
		"""
		vercel_messages = VercelMessageSerializer.serialize_messages(messages)

		try:
			model_params: dict[str, Any] = {}
			if self.temperature is not None:
				model_params['temperature'] = self.temperature
			if self.max_tokens is not None:
				model_params['max_tokens'] = self.max_tokens
			if self.top_p is not None:
				model_params['top_p'] = self.top_p

			extra_body: dict[str, Any] = {}

			provider_opts: dict[str, Any] = {}
			if self.provider_options:
				provider_opts.update(self.provider_options)

			if self.reasoning:
				# Merge provider-specific reasoning options (ex: {'anthropic': {'thinking': ...}})
				for provider_name, opts in self.reasoning.items():
					existing = provider_opts.get(provider_name, {})
					existing.update(opts)
					provider_opts[provider_name] = existing

			gateway_opts: dict[str, Any] = provider_opts.get('gateway', {})

			if self.model_fallbacks:
				gateway_opts['models'] = self.model_fallbacks

			if self.caching:
				gateway_opts['caching'] = self.caching

			if gateway_opts:
				provider_opts['gateway'] = gateway_opts

			if provider_opts:
				extra_body['providerOptions'] = provider_opts

			if extra_body:
				model_params['extra_body'] = extra_body

			if output_format is None:
				# Return string response
				response = await self.get_client().chat.completions.create(
					model=self.model,
					messages=vercel_messages,
					**model_params,
				)

				usage = self._get_usage(response)
				return ChatInvokeCompletion(
					completion=response.choices[0].message.content or '',
					usage=usage,
					stop_reason=response.choices[0].finish_reason if response.choices else None,
				)

			else:
				is_google_model = self.model.startswith('google/')
				is_anthropic_model = self.model.startswith('anthropic/')
				is_reasoning_model = self.reasoning_models and any(
					str(pattern).lower() in str(self.model).lower() for pattern in self.reasoning_models
				)

				if is_google_model or is_anthropic_model or is_reasoning_model:
					modified_messages = [m.model_copy(deep=True) for m in messages]

					schema = SchemaOptimizer.create_gemini_optimized_schema(output_format)
					json_instruction = f'\n\nIMPORTANT: You must respond with ONLY a valid JSON object (no markdown, no code blocks, no explanations) that exactly matches this schema:\n{json.dumps(schema, indent=2)}'

					instruction_added = False
					if modified_messages and modified_messages[0].role == 'system':
						if isinstance(modified_messages[0].content, str):
							modified_messages[0].content += json_instruction
							instruction_added = True
						elif isinstance(modified_messages[0].content, list):
							modified_messages[0].content.append(ContentPartTextParam(text=json_instruction))
							instruction_added = True
					elif modified_messages and modified_messages[-1].role == 'user':
						if isinstance(modified_messages[-1].content, str):
							modified_messages[-1].content += json_instruction
							instruction_added = True
						elif isinstance(modified_messages[-1].content, list):
							modified_messages[-1].content.append(ContentPartTextParam(text=json_instruction))
							instruction_added = True

					if not instruction_added:
						modified_messages.insert(0, SystemMessage(content=json_instruction))

					vercel_messages = VercelMessageSerializer.serialize_messages(modified_messages)

					response = await self.get_client().chat.completions.create(
						model=self.model,
						messages=vercel_messages,
						**model_params,
					)

					content = response.choices[0].message.content if response.choices else None

					if not content:
						raise ModelProviderError(
							message='No response from model',
							status_code=500,
							model=self.name,
						)

					try:
						text = content.strip()
						if text.startswith('```json') and text.endswith('```'):
							text = text[7:-3].strip()
						elif text.startswith('```') and text.endswith('```'):
							text = text[3:-3].strip()

						parsed_data = json.loads(text)
						parsed = output_format.model_validate(parsed_data)

						usage = self._get_usage(response)
						return ChatInvokeCompletion(
							completion=parsed,
							usage=usage,
							stop_reason=response.choices[0].finish_reason if response.choices else None,
						)

					except (json.JSONDecodeError, ValueError) as e:
						raise ModelProviderError(
							message=f'Failed to parse JSON response: {str(e)}. Raw response: {content[:200]}',
							status_code=500,
							model=self.name,
						) from e

				else:
					schema = SchemaOptimizer.create_optimized_json_schema(output_format)

					response_format_schema: JSONSchema = {
						'name': 'agent_output',
						'strict': True,
						'schema': schema,
					}

					response = await self.get_client().chat.completions.create(
						model=self.model,
						messages=vercel_messages,
						response_format=ResponseFormatJSONSchema(
							json_schema=response_format_schema,
							type='json_schema',
						),
						**model_params,
					)

					content = response.choices[0].message.content if response.choices else None

					if not content:
						raise ModelProviderError(
							message='Failed to parse structured output from model response - empty or null content',
							status_code=500,
							model=self.name,
						)

					usage = self._get_usage(response)
					parsed = output_format.model_validate_json(content)

					return ChatInvokeCompletion(
						completion=parsed,
						usage=usage,
						stop_reason=response.choices[0].finish_reason if response.choices else None,
					)

		except RateLimitError as e:
			raise ModelRateLimitError(message=e.message, model=self.name) from e

		except APIConnectionError as e:
			raise ModelProviderError(message=str(e), model=self.name) from e

		except APIStatusError as e:
			raise ModelProviderError(message=e.message, status_code=e.status_code, model=self.name) from e

		except Exception as e:
			raise ModelProviderError(message=str(e), model=self.name) from e