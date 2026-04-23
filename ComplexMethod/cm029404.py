async def input(
			params: InputTextAction,
			browser_session: BrowserSession,
			has_sensitive_data: bool = False,
			sensitive_data: dict[str, str | dict[str, str]] | None = None,
		):
			# Look up the node from the selector map
			node = await browser_session.get_element_by_index(params.index)
			if node is None:
				msg = f'Element index {params.index} not available - page may have changed. Try refreshing browser state.'
				logger.warning(f'⚠️ {msg}')
				return ActionResult(extracted_content=msg)

			# Highlight the element being typed into (truly non-blocking)
			create_task_with_error_handling(
				browser_session.highlight_interaction_element(node), name='highlight_type_element', suppress_exceptions=True
			)

			# Dispatch type text event with node
			try:
				# Detect which sensitive key is being used
				sensitive_key_name = None
				if has_sensitive_data and sensitive_data:
					sensitive_key_name = _detect_sensitive_key_name(params.text, sensitive_data)

				event = browser_session.event_bus.dispatch(
					TypeTextEvent(
						node=node,
						text=params.text,
						clear=params.clear,
						is_sensitive=has_sensitive_data,
						sensitive_key_name=sensitive_key_name,
					)
				)
				await event
				input_metadata = await event.event_result(raise_if_any=True, raise_if_none=False)

				# Create message with sensitive data handling
				if has_sensitive_data:
					if sensitive_key_name:
						msg = f'Typed {sensitive_key_name}'
						log_msg = f'Typed <{sensitive_key_name}>'
					else:
						msg = 'Typed sensitive data'
						log_msg = 'Typed <sensitive>'
				else:
					msg = f"Typed '{params.text}'"
					log_msg = f"Typed '{params.text}'"

				logger.debug(log_msg)

				# Check for value mismatch (non-sensitive only)
				actual_value = None
				if isinstance(input_metadata, dict):
					actual_value = input_metadata.pop('actual_value', None)

				if not has_sensitive_data and actual_value is not None and actual_value != params.text:
					msg += f"\n⚠️ Note: the field's actual value '{actual_value}' differs from typed text '{params.text}'. The page may have reformatted or autocompleted your input."

				# Check for autocomplete/combobox field — add mechanical delay for dropdown
				if _is_autocomplete_field(node):
					msg += '\n💡 This is an autocomplete field. Wait for suggestions to appear, then click the correct suggestion instead of pressing Enter.'
					# Only delay for true JS-driven autocomplete (combobox / aria-autocomplete),
					# not native <datalist> or loose aria-haspopup which the browser handles instantly
					attrs = node.attributes or {}
					if attrs.get('role') == 'combobox' or (attrs.get('aria-autocomplete', '') not in ('', 'none')):
						await asyncio.sleep(0.4)  # let JS dropdown populate before next action

				# Include input coordinates in metadata if available
				return ActionResult(
					extracted_content=msg,
					long_term_memory=msg,
					metadata=input_metadata if isinstance(input_metadata, dict) else None,
				)
			except BrowserError as e:
				return handle_browser_error(e)
			except Exception as e:
				# Log the full error for debugging
				logger.error(f'Failed to dispatch TypeTextEvent: {type(e).__name__}: {e}')
				error_msg = f'Failed to type text into element {params.index}: {e}'
				return ActionResult(error=error_msg)