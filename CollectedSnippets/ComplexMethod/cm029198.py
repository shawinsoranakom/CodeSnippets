async def wrapper(*args, **kwargs) -> T:
			# 1. Get API key
			api_key = BROWSER_USE_API_KEY or os.getenv('BROWSER_USE_API_KEY')
			if not api_key:
				raise SandboxError('BROWSER_USE_API_KEY is required')

			# 2. Extract all parameters (explicit + closure)
			all_params = _extract_all_params(func, args, kwargs)

			# 3. Get function source without decorator and only needed imports
			func_source = _get_function_source_without_decorator(func)
			needed_imports = _get_imports_used_in_function(func)

			# Always include Browser import since it's required for the function signature
			if needed_imports:
				needed_imports = 'from browser_use import Browser\n' + needed_imports
			else:
				needed_imports = 'from browser_use import Browser'

			# 4. Pickle parameters using cloudpickle for robust serialization
			pickled_params = base64.b64encode(cloudpickle.dumps(all_params)).decode()

			# 5. Determine which params are in the function signature vs closure/globals
			func_param_names = {p.name for p in sig.parameters.values() if p.name != 'browser'}
			non_explicit_params = {k: v for k, v in all_params.items() if k not in func_param_names}
			explicit_params = {k: v for k, v in all_params.items() if k in func_param_names}

			# Inject closure variables and globals as module-level vars
			var_injections = []
			for var_name in non_explicit_params.keys():
				var_injections.append(f"{var_name} = _params['{var_name}']")

			var_injection_code = '\n'.join(var_injections) if var_injections else '# No closure variables or globals'

			# Build function call
			if explicit_params:
				function_call = (
					f'await {func.__name__}(browser=browser, **{{k: _params[k] for k in {list(explicit_params.keys())!r}}})'
				)
			else:
				function_call = f'await {func.__name__}(browser=browser)'

			# 6. Create wrapper code that unpickles params and calls function
			execution_code = f"""import cloudpickle
import base64

# Imports used in function
{needed_imports}

# Unpickle all parameters (explicit, closure, and globals)
_pickled_params = base64.b64decode({repr(pickled_params)})
_params = cloudpickle.loads(_pickled_params)

# Inject closure variables and globals into module scope
{var_injection_code}

# Original function (decorator removed)
{func_source}

# Wrapper function that passes explicit params
async def run(browser):
	return {function_call}

"""

			# 9. Send to server
			payload: dict[str, Any] = {'code': base64.b64encode(execution_code.encode()).decode()}

			combined_env: dict[str, str] = env_vars.copy() if env_vars else {}
			combined_env['LOG_LEVEL'] = log_level.upper()
			payload['env'] = combined_env

			# Add cloud parameters if provided
			if cloud_profile_id is not None:
				payload['cloud_profile_id'] = cloud_profile_id
			if cloud_proxy_country_code is not None:
				payload['cloud_proxy_country_code'] = cloud_proxy_country_code
			if cloud_timeout is not None:
				payload['cloud_timeout'] = cloud_timeout

			url = server_url or 'https://sandbox.api.browser-use.com/sandbox-stream'

			request_headers = {'X-API-Key': api_key}
			if headers:
				request_headers.update(headers)

			# 10. Handle SSE streaming
			_NO_RESULT = object()
			execution_result = _NO_RESULT
			live_url_shown = False
			execution_started = False
			received_final_event = False

			async with httpx.AsyncClient(timeout=1800.0) as client:
				async with client.stream('POST', url, json=payload, headers=request_headers) as response:
					response.raise_for_status()

					try:
						async for line in response.aiter_lines():
							if not line or not line.startswith('data: '):
								continue

							event_json = line[6:]
							try:
								event = SSEEvent.from_json(event_json)

								if event.type == SSEEventType.BROWSER_CREATED:
									assert isinstance(event.data, BrowserCreatedData)

									if on_browser_created:
										try:
											await _call_callback(on_browser_created, event.data)
										except Exception as e:
											if not quiet:
												print(f'⚠️  Error in on_browser_created callback: {e}')

									if not quiet and event.data.live_url and not live_url_shown:
										width = get_terminal_width()
										print('\n' + '━' * width)
										print('👁️  LIVE BROWSER VIEW (Click to watch)')
										print(f'🔗 {event.data.live_url}')
										print('━' * width)
										live_url_shown = True

								elif event.type == SSEEventType.LOG:
									assert isinstance(event.data, LogData)
									message = event.data.message
									level = event.data.level

									if on_log:
										try:
											await _call_callback(on_log, event.data)
										except Exception as e:
											if not quiet:
												print(f'⚠️  Error in on_log callback: {e}')

									if level == 'stdout':
										if not quiet:
											if not execution_started:
												width = get_terminal_width()
												print('\n' + '─' * width)
												print('⚡ Runtime Output')
												print('─' * width)
												execution_started = True
											print(f'  {message}', end='')
									elif level == 'stderr':
										if not quiet:
											if not execution_started:
												width = get_terminal_width()
												print('\n' + '─' * width)
												print('⚡ Runtime Output')
												print('─' * width)
												execution_started = True
											print(f'⚠️  {message}', end='', file=sys.stderr)
									elif level == 'info':
										if not quiet:
											if 'credit' in message.lower():
												import re

												match = re.search(r'\$[\d,]+\.?\d*', message)
												if match:
													print(f'💰 You have {match.group()} credits')
											else:
												print(f'ℹ️  {message}')
									else:
										if not quiet:
											print(f'  {message}')

								elif event.type == SSEEventType.INSTANCE_READY:
									if on_instance_ready:
										try:
											await _call_callback(on_instance_ready)
										except Exception as e:
											if not quiet:
												print(f'⚠️  Error in on_instance_ready callback: {e}')

									if not quiet:
										print('✅ Browser ready, starting execution...\n')

								elif event.type == SSEEventType.RESULT:
									assert isinstance(event.data, ResultData)
									exec_response = event.data.execution_response
									received_final_event = True

									if on_result:
										try:
											await _call_callback(on_result, event.data)
										except Exception as e:
											if not quiet:
												print(f'⚠️  Error in on_result callback: {e}')

									if exec_response.success:
										execution_result = exec_response.result
										if not quiet and execution_started:
											width = get_terminal_width()
											print('\n' + '─' * width)
											print()
									else:
										error_msg = exec_response.error or 'Unknown error'
										raise SandboxError(f'Execution failed: {error_msg}')

								elif event.type == SSEEventType.ERROR:
									assert isinstance(event.data, ErrorData)
									received_final_event = True

									if on_error:
										try:
											await _call_callback(on_error, event.data)
										except Exception as e:
											if not quiet:
												print(f'⚠️  Error in on_error callback: {e}')

									raise SandboxError(f'Execution failed: {event.data.error}')

							except (json.JSONDecodeError, ValueError):
								continue

					except (httpx.RemoteProtocolError, httpx.ReadError, httpx.StreamClosed) as e:
						# With deterministic handshake, these should never happen
						# If they do, it's a real error
						raise SandboxError(
							f'Stream error: {e.__class__.__name__}: {e or "connection closed unexpectedly"}'
						) from e

			# 11. Parse result with type annotation
			if execution_result is not _NO_RESULT:
				return_annotation = func.__annotations__.get('return')
				if return_annotation:
					parsed_result = _parse_with_type_annotation(execution_result, return_annotation)
					return parsed_result
				return execution_result  # type: ignore[return-value]

			raise SandboxError('No result received from execution')