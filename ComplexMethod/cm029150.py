async def _make_api_call():
			start_time = time.time()
			self.logger.debug(f'🚀 Starting API call to {self.model}')

			try:
				if output_format is None:
					# Return string response
					self.logger.debug('📄 Requesting text response')

					response = await self.get_client().aio.models.generate_content(
						model=self.model,
						contents=contents,  # type: ignore
						config=config,
					)

					elapsed = time.time() - start_time
					self.logger.debug(f'✅ Got text response in {elapsed:.2f}s')

					# Handle case where response.text might be None
					text = response.text or ''
					if not text:
						self.logger.warning('⚠️ Empty text response received')

					usage = self._get_usage(response)

					return ChatInvokeCompletion(
						completion=text,
						usage=usage,
						stop_reason=self._get_stop_reason(response),
					)

				else:
					# Handle structured output
					if self.supports_structured_output:
						# Use native JSON mode
						self.logger.debug(f'🔧 Requesting structured output for {output_format.__name__}')
						config['response_mime_type'] = 'application/json'
						# Convert Pydantic model to Gemini-compatible schema
						optimized_schema = SchemaOptimizer.create_gemini_optimized_schema(output_format)

						gemini_schema = self._fix_gemini_schema(optimized_schema)
						config['response_schema'] = gemini_schema

						response = await self.get_client().aio.models.generate_content(
							model=self.model,
							contents=contents,
							config=config,
						)

						elapsed = time.time() - start_time
						self.logger.debug(f'✅ Got structured response in {elapsed:.2f}s')

						usage = self._get_usage(response)

						# Handle case where response.parsed might be None
						if response.parsed is None:
							self.logger.debug('📝 Parsing JSON from text response')
							# When using response_schema, Gemini returns JSON as text
							if response.text:
								try:
									# Handle JSON wrapped in markdown code blocks (common Gemini behavior)
									text = response.text.strip()
									if text.startswith('```json') and text.endswith('```'):
										text = text[7:-3].strip()
										self.logger.debug('🔧 Stripped ```json``` wrapper from response')
									elif text.startswith('```') and text.endswith('```'):
										text = text[3:-3].strip()
										self.logger.debug('🔧 Stripped ``` wrapper from response')

									# Parse the JSON text and validate with the Pydantic model
									parsed_data = json.loads(text)
									return ChatInvokeCompletion(
										completion=output_format.model_validate(parsed_data),
										usage=usage,
										stop_reason=self._get_stop_reason(response),
									)
								except (json.JSONDecodeError, ValueError) as e:
									self.logger.error(f'❌ Failed to parse JSON response: {str(e)}')
									self.logger.debug(f'Raw response text: {response.text[:200]}...')
									raise ModelProviderError(
										message=f'Failed to parse or validate response {response}: {str(e)}',
										status_code=500,
										model=self.model,
									) from e
							else:
								self.logger.error('❌ No response text received')
								raise ModelProviderError(
									message=f'No response from model {response}',
									status_code=500,
									model=self.model,
								)

						# Ensure we return the correct type
						if isinstance(response.parsed, output_format):
							return ChatInvokeCompletion(
								completion=response.parsed,
								usage=usage,
								stop_reason=self._get_stop_reason(response),
							)
						else:
							# If it's not the expected type, try to validate it
							return ChatInvokeCompletion(
								completion=output_format.model_validate(response.parsed),
								usage=usage,
								stop_reason=self._get_stop_reason(response),
							)
					else:
						# Fallback: Request JSON in the prompt for models without native JSON mode
						self.logger.debug(f'🔄 Using fallback JSON mode for {output_format.__name__}')
						# Create a copy of messages to modify
						modified_messages = [m.model_copy(deep=True) for m in messages]

						# Add JSON instruction to the last message
						if modified_messages and isinstance(modified_messages[-1].content, str):
							json_instruction = f'\n\nPlease respond with a valid JSON object that matches this schema: {SchemaOptimizer.create_optimized_json_schema(output_format)}'
							modified_messages[-1].content += json_instruction

						# Re-serialize with modified messages
						fallback_contents, fallback_system = GoogleMessageSerializer.serialize_messages(
							modified_messages, include_system_in_user=self.include_system_in_user
						)

						# Update config with fallback system instruction if present
						fallback_config = config.copy()
						if fallback_system:
							fallback_config['system_instruction'] = fallback_system

						response = await self.get_client().aio.models.generate_content(
							model=self.model,
							contents=fallback_contents,  # type: ignore
							config=fallback_config,
						)

						elapsed = time.time() - start_time
						self.logger.debug(f'✅ Got fallback response in {elapsed:.2f}s')

						usage = self._get_usage(response)

						# Try to extract JSON from the text response
						if response.text:
							try:
								# Try to find JSON in the response
								text = response.text.strip()

								# Common patterns: JSON wrapped in markdown code blocks
								if text.startswith('```json') and text.endswith('```'):
									text = text[7:-3].strip()
								elif text.startswith('```') and text.endswith('```'):
									text = text[3:-3].strip()

								# Parse and validate
								parsed_data = json.loads(text)
								return ChatInvokeCompletion(
									completion=output_format.model_validate(parsed_data),
									usage=usage,
									stop_reason=self._get_stop_reason(response),
								)
							except (json.JSONDecodeError, ValueError) as e:
								self.logger.error(f'❌ Failed to parse fallback JSON: {str(e)}')
								self.logger.debug(f'Raw response text: {response.text[:200]}...')
								raise ModelProviderError(
									message=f'Model does not support JSON mode and failed to parse JSON from text response: {str(e)}',
									status_code=500,
									model=self.model,
								) from e
						else:
							self.logger.error('❌ No response text in fallback mode')
							raise ModelProviderError(
								message='No response from model',
								status_code=500,
								model=self.model,
							)
			except Exception as e:
				elapsed = time.time() - start_time
				self.logger.error(f'💥 API call failed after {elapsed:.2f}s: {type(e).__name__}: {e}')
				# Re-raise the exception
				raise