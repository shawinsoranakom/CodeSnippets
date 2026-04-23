async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		"""
		Invoke the LangChain model with the given messages.

		Args:
			messages: List of browser-use chat messages
			output_format: Optional Pydantic model class for structured output (not supported in basic LangChain integration)

		Returns:
			Either a string response or an instance of output_format
		"""

		# Convert browser-use messages to LangChain messages
		langchain_messages = LangChainMessageSerializer.serialize_messages(messages)

		try:
			if output_format is None:
				# Return string response
				response = await self.chat.ainvoke(langchain_messages)  # type: ignore

				# Import at runtime for isinstance check
				from langchain_core.messages import AIMessage as LangChainAIMessage  # type: ignore

				if not isinstance(response, LangChainAIMessage):
					raise ModelProviderError(
						message=f'Response is not an AIMessage: {type(response)}',
						model=self.name,
					)

				# Extract content from LangChain response
				content = response.content if hasattr(response, 'content') else str(response)

				usage = self._get_usage(response)
				return ChatInvokeCompletion(
					completion=str(content),
					usage=usage,
				)

			else:
				# Use LangChain's structured output capability
				try:
					structured_chat = self.chat.with_structured_output(output_format)
					parsed_object = await structured_chat.ainvoke(langchain_messages)

					# For structured output, usage metadata is typically not available
					# in the parsed object since it's a Pydantic model, not an AIMessage
					usage = None

					# Type cast since LangChain's with_structured_output returns the correct type
					return ChatInvokeCompletion(
						completion=parsed_object,  # type: ignore
						usage=usage,
					)
				except AttributeError:
					# Fall back to manual parsing if with_structured_output is not available
					response = await self.chat.ainvoke(langchain_messages)  # type: ignore

					if not isinstance(response, 'LangChainAIMessage'):
						raise ModelProviderError(
							message=f'Response is not an AIMessage: {type(response)}',
							model=self.name,
						)

					content = response.content if hasattr(response, 'content') else str(response)

					try:
						if isinstance(content, str):
							import json

							parsed_data = json.loads(content)
							if isinstance(parsed_data, dict):
								parsed_object = output_format(**parsed_data)
							else:
								raise ValueError('Parsed JSON is not a dictionary')
						else:
							raise ValueError('Content is not a string and structured output not supported')
					except Exception as e:
						raise ModelProviderError(
							message=f'Failed to parse response as {output_format.__name__}: {e}',
							model=self.name,
						) from e

					usage = self._get_usage(response)
					return ChatInvokeCompletion(
						completion=parsed_object,
						usage=usage,
					)

		except Exception as e:
			# Convert any LangChain errors to browser-use ModelProviderError
			raise ModelProviderError(
				message=f'LangChain model error: {str(e)}',
				model=self.name,
			) from e