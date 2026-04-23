async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None, **kwargs: Any
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		"""
		Invoke the OCI GenAI model with the given messages using raw API.

		Args:
		    messages: List of chat messages
		    output_format: Optional Pydantic model class for structured output

		Returns:
		    Either a string response or an instance of output_format
		"""
		try:
			if output_format is None:
				# Return string response
				response = await self._make_request(messages)
				content = self._extract_content(response)
				usage = self._extract_usage(response)

				return ChatInvokeCompletion(
					completion=content,
					usage=usage,
				)
			else:
				# For structured output, add JSON schema instructions
				optimized_schema = SchemaOptimizer.create_optimized_json_schema(output_format)

				# Add JSON schema instruction to messages
				system_instruction = f"""
You must respond with ONLY a valid JSON object that matches this exact schema:
{json.dumps(optimized_schema, indent=2)}

IMPORTANT: 
- Your response must be ONLY the JSON object, no additional text
- The JSON must be valid and parseable
- All required fields must be present
- No extra fields are allowed
- Use proper JSON syntax with double quotes
"""

				# Clone messages and add system instruction
				modified_messages = messages.copy()

				# Add or modify system message
				from browser_use.llm.messages import SystemMessage

				if modified_messages and hasattr(modified_messages[0], 'role') and modified_messages[0].role == 'system':
					# Modify existing system message
					existing_content = modified_messages[0].content
					if isinstance(existing_content, str):
						modified_messages[0].content = existing_content + '\n\n' + system_instruction
					else:
						# Handle list content
						modified_messages[0].content = str(existing_content) + '\n\n' + system_instruction
				else:
					# Insert new system message at the beginning
					modified_messages.insert(0, SystemMessage(content=system_instruction))

				response = await self._make_request(modified_messages)
				response_text = self._extract_content(response)

				# Clean and parse the JSON response
				try:
					# Clean the response text
					cleaned_text = response_text.strip()

					# Remove markdown code blocks if present
					if cleaned_text.startswith('```json'):
						cleaned_text = cleaned_text[7:]
					if cleaned_text.startswith('```'):
						cleaned_text = cleaned_text[3:]
					if cleaned_text.endswith('```'):
						cleaned_text = cleaned_text[:-3]

					cleaned_text = cleaned_text.strip()

					# Try to find JSON object in the response
					if not cleaned_text.startswith('{'):
						start_idx = cleaned_text.find('{')
						end_idx = cleaned_text.rfind('}')
						if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
							cleaned_text = cleaned_text[start_idx : end_idx + 1]

					# Parse the JSON
					parsed_data = json.loads(cleaned_text)
					parsed = output_format.model_validate(parsed_data)

					usage = self._extract_usage(response)
					return ChatInvokeCompletion(
						completion=parsed,
						usage=usage,
					)

				except (json.JSONDecodeError, ValueError) as e:
					raise ModelProviderError(
						message=f'Failed to parse structured output: {str(e)}. Response was: {response_text[:200]}...',
						status_code=500,
						model=self.name,
					) from e

		except ModelRateLimitError:
			# Re-raise rate limit errors as-is
			raise
		except ModelProviderError:
			# Re-raise provider errors as-is
			raise
		except Exception as e:
			# Handle any other exceptions
			raise ModelProviderError(
				message=f'Unexpected error: {str(e)}',
				status_code=500,
				model=self.name,
			) from e