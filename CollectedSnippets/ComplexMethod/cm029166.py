async def ainvoke(
		self, messages: list[BaseMessage], output_format: type[T] | None = None, **kwargs: Any
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		"""
		Invoke the AWS Bedrock model with the given messages.

		Args:
			messages: List of chat messages
			output_format: Optional Pydantic model class for structured output

		Returns:
			Either a string response or an instance of output_format
		"""
		try:
			from botocore.exceptions import ClientError  # type: ignore
		except ImportError:
			raise ImportError(
				'`boto3` not installed. Please install using `pip install browser-use[aws] or pip install browser-use[all]`'
			)

		bedrock_messages, system_message = AWSBedrockMessageSerializer.serialize_messages(messages)

		try:
			# Prepare the request body
			body: dict[str, Any] = {}

			if system_message:
				body['system'] = system_message

			inference_config = self._get_inference_config()
			if inference_config:
				body['inferenceConfig'] = inference_config

			# Handle structured output via tool calling
			if output_format is not None:
				tools = self._format_tools_for_request(output_format)
				body['toolConfig'] = {'tools': tools}

			# Add any additional request parameters
			if self.request_params:
				body.update(self.request_params)

			# Filter out None values
			body = {k: v for k, v in body.items() if v is not None}

			# Make the API call
			client = self._get_client()
			response = client.converse(modelId=self.model, messages=bedrock_messages, **body)

			usage = self._get_usage(response)

			# Extract the response content
			if 'output' in response and 'message' in response['output']:
				message = response['output']['message']
				content = message.get('content', [])

				if output_format is None:
					# Return text response
					text_content = []
					for item in content:
						if 'text' in item:
							text_content.append(item['text'])

					response_text = '\n'.join(text_content) if text_content else ''
					return ChatInvokeCompletion(
						completion=response_text,
						usage=usage,
					)
				else:
					# Handle structured output from tool calls
					for item in content:
						if 'toolUse' in item:
							tool_use = item['toolUse']
							tool_input = tool_use.get('input', {})

							try:
								# Validate and return the structured output
								return ChatInvokeCompletion(
									completion=output_format.model_validate(tool_input),
									usage=usage,
								)
							except Exception as e:
								# If validation fails, try to parse as JSON first
								if isinstance(tool_input, str):
									try:
										data = json.loads(tool_input)
										return ChatInvokeCompletion(
											completion=output_format.model_validate(data),
											usage=usage,
										)
									except json.JSONDecodeError:
										pass
								raise ModelProviderError(
									message=f'Failed to validate structured output: {str(e)}',
									model=self.name,
								) from e

					# If no tool use found but output_format was requested
					raise ModelProviderError(
						message='Expected structured output but no tool use found in response',
						model=self.name,
					)

			# If no valid content found
			if output_format is None:
				return ChatInvokeCompletion(
					completion='',
					usage=usage,
				)
			else:
				raise ModelProviderError(
					message='No valid content found in response',
					model=self.name,
				)

		except ClientError as e:
			error_code = e.response.get('Error', {}).get('Code', 'Unknown')
			error_message = e.response.get('Error', {}).get('Message', str(e))

			if error_code in ['ThrottlingException', 'TooManyRequestsException']:
				raise ModelRateLimitError(message=error_message, model=self.name) from e
			else:
				raise ModelProviderError(message=error_message, model=self.name) from e
		except Exception as e:
			raise ModelProviderError(message=str(e), model=self.name) from e