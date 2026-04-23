async def evaluate(code: str, browser_session: BrowserSession):
			# Execute JavaScript with proper error handling and promise support

			cdp_session = await browser_session.get_or_create_cdp_session()

			try:
				# Validate and potentially fix JavaScript code before execution
				validated_code = self._validate_and_fix_javascript(code)

				# Always use awaitPromise=True - it's ignored for non-promises
				result = await cdp_session.cdp_client.send.Runtime.evaluate(
					params={'expression': validated_code, 'returnByValue': True, 'awaitPromise': True},
					session_id=cdp_session.session_id,
				)

				# Check for JavaScript execution errors
				if result.get('exceptionDetails'):
					exception = result['exceptionDetails']
					error_msg = f'JavaScript execution error: {exception.get("text", "Unknown error")}'

					# Enhanced error message with debugging info
					enhanced_msg = f"""JavaScript Execution Failed:
{error_msg}

Validated Code (after quote fixing):
{validated_code[:500]}{'...' if len(validated_code) > 500 else ''}
"""

					logger.debug(enhanced_msg)
					return ActionResult(error=enhanced_msg)

				# Get the result data
				result_data = result.get('result', {})

				# Check for wasThrown flag (backup error detection)
				if result_data.get('wasThrown'):
					msg = f'JavaScript code: {code} execution failed (wasThrown=true)'
					logger.debug(msg)
					return ActionResult(error=msg)

				# Get the actual value
				value = result_data.get('value')

				# Handle different value types
				if value is None:
					# Could be legitimate null/undefined result
					result_text = str(value) if 'value' in result_data else 'undefined'
				elif isinstance(value, (dict, list)):
					# Complex objects - should be serialized by returnByValue
					try:
						result_text = json.dumps(value, ensure_ascii=False)
					except (TypeError, ValueError):
						# Fallback for non-serializable objects
						result_text = str(value)
				else:
					# Primitive values (string, number, boolean)
					result_text = str(value)

				import re

				image_pattern = r'(data:image/[^;]+;base64,[A-Za-z0-9+/=]+)'
				found_images = re.findall(image_pattern, result_text)

				metadata = None
				if found_images:
					# Store images in metadata so they can be added as ContentPartImageParam
					metadata = {'images': found_images}

					# Replace image data in result text with shorter placeholder
					modified_text = result_text
					for i, img_data in enumerate(found_images, 1):
						placeholder = '[Image]'
						modified_text = modified_text.replace(img_data, placeholder)
					result_text = modified_text

				# Apply length limit with better truncation (after image extraction)
				if len(result_text) > 20000:
					result_text = result_text[:19950] + '\n... [Truncated after 20000 characters]'

				# Don't log the code - it's already visible in the user's cell
				logger.debug(f'JavaScript executed successfully, result length: {len(result_text)}')

				# Memory handling: keep full result in extracted_content for current step,
				# but use truncated version in long_term_memory if too large
				MAX_MEMORY_LENGTH = 10000
				if len(result_text) < MAX_MEMORY_LENGTH:
					memory = result_text
					include_extracted_content_only_once = False
				else:
					memory = f'JavaScript executed successfully, result length: {len(result_text)} characters.'
					include_extracted_content_only_once = True

				# Return only the result, not the code (code is already in user's cell)
				return ActionResult(
					extracted_content=result_text,
					long_term_memory=memory,
					include_extracted_content_only_once=include_extracted_content_only_once,
					metadata=metadata,
				)

			except Exception as e:
				# CDP communication or other system errors
				error_msg = f'Failed to execute JavaScript: {type(e).__name__}: {e}'
				logger.debug(f'JavaScript code that failed: {code[:200]}...')
				return ActionResult(error=error_msg)