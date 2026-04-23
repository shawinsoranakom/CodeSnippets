async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None, **kwargs: Any
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		anthropic_messages, system_prompt = AnthropicMessageSerializer.serialize_messages(messages)

		try:
			if output_format is None:
				# Normal completion without structured output
				response = await self.get_client().messages.create(
					model=self.model,
					messages=anthropic_messages,
					system=system_prompt or omit,
					**self._get_client_params_for_invoke(),
				)

				# Ensure we have a valid Message object before accessing attributes
				if not isinstance(response, Message):
					raise ModelProviderError(
						message=f'Unexpected response type from Anthropic API: {type(response).__name__}. Response: {str(response)[:200]}',
						status_code=502,
						model=self.name,
					)

				usage = self._get_usage(response)

				# Extract text from the first content block
				first_content = response.content[0]
				if isinstance(first_content, TextBlock):
					response_text = first_content.text
				else:
					# If it's not a text block, convert to string
					response_text = str(first_content)

				return ChatInvokeCompletion(
					completion=response_text,
					usage=usage,
					stop_reason=response.stop_reason,
				)

			else:
				# Use tool calling for structured output
				# Create a tool that represents the output format
				tool_name = output_format.__name__
				schema = SchemaOptimizer.create_optimized_json_schema(output_format)

				# Remove title from schema if present (Anthropic doesn't like it in parameters)
				if 'title' in schema:
					del schema['title']

				tool = ToolParam(
					name=tool_name,
					description=f'Extract information in the format of {tool_name}',
					input_schema=schema,
					cache_control=CacheControlEphemeralParam(type='ephemeral'),
				)

				# Force the model to use this tool
				tool_choice = ToolChoiceToolParam(type='tool', name=tool_name)

				response = await self.get_client().messages.create(
					model=self.model,
					messages=anthropic_messages,
					tools=[tool],
					system=system_prompt or omit,
					tool_choice=tool_choice,
					**self._get_client_params_for_invoke(),
				)

				# Ensure we have a valid Message object before accessing attributes
				if not isinstance(response, Message):
					raise ModelProviderError(
						message=f'Unexpected response type from Anthropic API: {type(response).__name__}. Response: {str(response)[:200]}',
						status_code=502,
						model=self.name,
					)

				usage = self._get_usage(response)

				# Extract the tool use block
				for content_block in response.content:
					if hasattr(content_block, 'type') and content_block.type == 'tool_use':
						# Parse the tool input as the structured output
						try:
							return ChatInvokeCompletion(
								completion=output_format.model_validate(content_block.input),
								usage=usage,
								stop_reason=response.stop_reason,
							)
						except Exception as e:
							# If validation fails, try to fix common model output issues
							_input = content_block.input
							if isinstance(_input, str):
								_input = json.loads(_input)
							elif isinstance(_input, dict):
								# Model sometimes double-serializes fields
								for key, value in _input.items():
									if isinstance(value, str) and value.startswith(('[', '{')):
										try:
											_input[key] = json.loads(value)
										except json.JSONDecodeError:
											cleaned = value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
											try:
												_input[key] = json.loads(cleaned)
											except json.JSONDecodeError:
												pass
							else:
								raise
							return ChatInvokeCompletion(
								completion=output_format.model_validate(_input),
								usage=usage,
								stop_reason=response.stop_reason,
							)

				# If no tool use block found, raise an error
				raise ValueError('Expected tool use in response but none found')

		except APIConnectionError as e:
			raise ModelProviderError(message=e.message, model=self.name) from e
		except RateLimitError as e:
			raise ModelRateLimitError(message=e.message, model=self.name) from e
		except APIStatusError as e:
			raise ModelProviderError(message=e.message, status_code=e.status_code, model=self.name) from e
		except Exception as e:
			raise ModelProviderError(message=str(e), model=self.name) from e