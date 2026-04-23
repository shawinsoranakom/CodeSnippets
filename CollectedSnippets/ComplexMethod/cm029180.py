async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None, **kwargs: Any
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		"""
		Invoke the model with the given messages through OpenRouter.

		Args:
		    messages: List of chat messages
		    output_format: Optional Pydantic model class for structured output

		Returns:
		    Either a string response or an instance of output_format
		"""
		openrouter_messages = OpenRouterMessageSerializer.serialize_messages(messages)

		# Set up extra headers for OpenRouter
		extra_headers = {}
		if self.http_referer:
			extra_headers['HTTP-Referer'] = self.http_referer

		try:
			if output_format is None:
				# Return string response
				response = await self.get_client().chat.completions.create(
					model=self.model,
					messages=openrouter_messages,
					temperature=self.temperature,
					top_p=self.top_p,
					seed=self.seed,
					extra_headers=extra_headers,
					**(self.extra_body or {}),
				)

				usage = self._get_usage(response)
				return ChatInvokeCompletion(
					completion=response.choices[0].message.content or '',
					usage=usage,
				)

			else:
				# Create a JSON schema for structured output
				schema = SchemaOptimizer.create_optimized_json_schema(output_format)

				response_format_schema: JSONSchema = {
					'name': 'agent_output',
					'strict': True,
					'schema': schema,
				}

				# Return structured response
				response = await self.get_client().chat.completions.create(
					model=self.model,
					messages=openrouter_messages,
					temperature=self.temperature,
					top_p=self.top_p,
					seed=self.seed,
					response_format=ResponseFormatJSONSchema(
						json_schema=response_format_schema,
						type='json_schema',
					),
					extra_headers=extra_headers,
					**(self.extra_body or {}),
				)

				if response.choices[0].message.content is None:
					raise ModelProviderError(
						message='Failed to parse structured output from model response',
						status_code=500,
						model=self.name,
					)
				usage = self._get_usage(response)

				parsed = output_format.model_validate_json(response.choices[0].message.content)

				return ChatInvokeCompletion(
					completion=parsed,
					usage=usage,
				)

		except RateLimitError as e:
			raise ModelRateLimitError(message=e.message, model=self.name) from e

		except APIConnectionError as e:
			raise ModelProviderError(message=str(e), model=self.name) from e

		except APIStatusError as e:
			raise ModelProviderError(message=e.message, status_code=e.status_code, model=self.name) from e

		except Exception as e:
			raise ModelProviderError(message=str(e), model=self.name) from e