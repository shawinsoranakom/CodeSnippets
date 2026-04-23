async def on_TypeTextEvent(self, event: TypeTextEvent) -> dict | None:
		"""Handle text input request with CDP."""
		try:
			# Use the provided node
			element_node = event.node
			index_for_logging = element_node.backend_node_id or 'unknown'

			# Check if this is index 0 or a falsy index - type to the page (whatever has focus)
			if not element_node.backend_node_id or element_node.backend_node_id == 0:
				# Type to the page without focusing any specific element
				await self._type_to_page(event.text)
				# Log with sensitive data protection
				if event.is_sensitive:
					if event.sensitive_key_name:
						self.logger.info(f'⌨️ Typed <{event.sensitive_key_name}> to the page (current focus)')
					else:
						self.logger.info('⌨️ Typed <sensitive> to the page (current focus)')
				else:
					self.logger.info(f'⌨️ Typed "{event.text}" to the page (current focus)')
				return None  # No coordinates available for page typing
			else:
				try:
					# Try to type to the specific element
					input_metadata = await self._input_text_element_node_impl(
						element_node,
						event.text,
						clear=event.clear or (not event.text),
						is_sensitive=event.is_sensitive,
					)
					# Log with sensitive data protection
					if event.is_sensitive:
						if event.sensitive_key_name:
							self.logger.info(f'⌨️ Typed <{event.sensitive_key_name}> into element with index {index_for_logging}')
						else:
							self.logger.info(f'⌨️ Typed <sensitive> into element with index {index_for_logging}')
					else:
						self.logger.info(f'⌨️ Typed "{event.text}" into element with index {index_for_logging}')
					self.logger.debug(f'Element xpath: {element_node.xpath}')
					return input_metadata  # Return coordinates if available
				except Exception as e:
					# Element not found or error - fall back to typing to the page
					self.logger.warning(f'Failed to type to element {index_for_logging}: {e}. Falling back to page typing.')
					try:
						await asyncio.wait_for(self._click_element_node_impl(element_node), timeout=10.0)
					except Exception as e:
						pass
					await self._type_to_page(event.text)
					# Log with sensitive data protection
					if event.is_sensitive:
						if event.sensitive_key_name:
							self.logger.info(f'⌨️ Typed <{event.sensitive_key_name}> to the page as fallback')
						else:
							self.logger.info('⌨️ Typed <sensitive> to the page as fallback')
					else:
						self.logger.info(f'⌨️ Typed "{event.text}" to the page as fallback')
					return None  # No coordinates available for fallback typing

			# Note: We don't clear cached state here - let multi_act handle DOM change detection
			# by explicitly rebuilding and comparing when needed
		except Exception as e:
			raise