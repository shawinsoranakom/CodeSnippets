async def ainvoke(
		self,
		messages: list[BaseMessage],
		output_format: type[T] | None = None,
		request_type: str = 'browser_agent',
		**kwargs: Any,
	) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
		"""
		Send request to browser-use cloud API.

		Args:
			messages: List of messages to send
			output_format: Expected output format (Pydantic model)
			request_type: Type of request - 'browser_agent' or 'judge'
			**kwargs: Additional arguments, including:
				- session_id: Session ID for sticky routing (same session → same container)

		Returns:
			ChatInvokeCompletion with structured response and usage info
		"""
		# Get ANONYMIZED_TELEMETRY setting from config
		from browser_use.config import CONFIG

		anonymized_telemetry = CONFIG.ANONYMIZED_TELEMETRY

		# Extract session_id from kwargs for sticky routing
		session_id = kwargs.get('session_id')

		# Prepare request payload
		payload: dict[str, Any] = {
			'model': self.model,
			'messages': [self._serialize_message(msg) for msg in messages],
			'fast': self.fast,
			'request_type': request_type,
			'anonymized_telemetry': anonymized_telemetry,
		}

		# Add session_id for sticky routing if provided
		if session_id:
			payload['session_id'] = session_id

		# Add output format schema if provided
		if output_format is not None:
			payload['output_format'] = output_format.model_json_schema()

		last_error: Exception | None = None

		# Retry loop with exponential backoff
		for attempt in range(self.max_retries):
			try:
				result = await self._make_request(payload)
				break
			except httpx.HTTPStatusError as e:
				last_error = e
				status_code = e.response.status_code

				# Check if this is a retryable error
				if status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries - 1:
					delay = min(self.retry_base_delay * (2**attempt), self.retry_max_delay)
					jitter = random.uniform(0, delay * 0.1)
					total_delay = delay + jitter
					logger.warning(
						f'⚠️ Got {status_code} error, retrying in {total_delay:.1f}s... (attempt {attempt + 1}/{self.max_retries})'
					)
					await asyncio.sleep(total_delay)
					continue

				# Non-retryable HTTP error or exhausted retries
				self._raise_http_error(e)

			except (httpx.TimeoutException, httpx.ConnectError) as e:
				last_error = e
				# Network errors are retryable
				if attempt < self.max_retries - 1:
					delay = min(self.retry_base_delay * (2**attempt), self.retry_max_delay)
					jitter = random.uniform(0, delay * 0.1)
					total_delay = delay + jitter
					error_type = 'timeout' if isinstance(e, httpx.TimeoutException) else 'connection error'
					logger.warning(
						f'⚠️ Got {error_type}, retrying in {total_delay:.1f}s... (attempt {attempt + 1}/{self.max_retries})'
					)
					await asyncio.sleep(total_delay)
					continue

				# Exhausted retries
				if isinstance(e, httpx.TimeoutException):
					raise ValueError(f'Request timed out after {self.timeout}s (retried {self.max_retries} times)')
				raise ValueError(f'Failed to connect to browser-use API after {self.max_retries} attempts: {e}')

			except Exception as e:
				raise ValueError(f'Failed to connect to browser-use API: {e}')
		else:
			# Loop completed without break (all retries exhausted)
			if last_error is not None:
				if isinstance(last_error, httpx.HTTPStatusError):
					self._raise_http_error(last_error)
				raise ValueError(f'Request failed after {self.max_retries} attempts: {last_error}')
			raise RuntimeError('Retry loop completed without return or exception')

		# Parse response - server returns structured data as dict
		if output_format is not None:
			# Server returns structured data as a dict, validate it
			completion_data = result['completion']
			logger.debug(
				f'📥 Got structured data from service: {list(completion_data.keys()) if isinstance(completion_data, dict) else type(completion_data)}'
			)

			# Convert action dicts to ActionModel instances if needed
			# llm-use returns dicts to avoid validation with empty ActionModel
			if isinstance(completion_data, dict) and 'action' in completion_data:
				actions = completion_data['action']
				if actions and isinstance(actions[0], dict):
					from typing import get_args

					# Get ActionModel type from output_format
					action_model_type = get_args(output_format.model_fields['action'].annotation)[0]

					# Convert dicts to ActionModel instances
					completion_data['action'] = [action_model_type.model_validate(action_dict) for action_dict in actions]

			completion = output_format.model_validate(completion_data)
		else:
			completion = result['completion']

		# Parse usage info
		usage = None
		if 'usage' in result and result['usage'] is not None:
			from browser_use.llm.views import ChatInvokeUsage

			usage = ChatInvokeUsage(**result['usage'])

		return ChatInvokeCompletion(
			completion=completion,
			usage=usage,
		)