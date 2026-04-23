async def on_ClickElementEvent(self, event: ClickElementEvent) -> dict | None:
		"""Handle click request with CDP. Automatically waits for file downloads if triggered."""
		try:
			# Check if session is alive before attempting any operations
			if not self.browser_session.agent_focus_target_id:
				error_msg = 'Cannot execute click: browser session is corrupted (target_id=None). Session may have crashed.'
				self.logger.error(f'{error_msg}')
				raise BrowserError(error_msg)

			# Use the provided node
			element_node = event.node
			index_for_logging = element_node.backend_node_id or 'unknown'

			# Check if element is a file input (should not be clicked)
			if self.browser_session.is_file_input(element_node):
				msg = f'Index {index_for_logging} - has an element which opens file upload dialog. To upload files please use a specific function to upload files'
				self.logger.info(f'{msg}')
				return {'validation_error': msg}

			# Detect print-related elements and handle them specially
			is_print_element = self._is_print_related_element(element_node)
			if is_print_element:
				self.logger.info(
					f'🖨️ Detected print button (index {index_for_logging}), generating PDF directly instead of opening dialog...'
				)
				click_metadata = await self._handle_print_button_click(element_node)
				if click_metadata and click_metadata.get('pdf_generated'):
					msg = f'Generated PDF: {click_metadata.get("path")}'
					self.logger.info(f'💾 {msg}')
					return click_metadata
				else:
					self.logger.warning('⚠️ PDF generation failed, falling back to regular click')

			# Execute click with automatic download detection
			click_metadata = await self._execute_click_with_download_detection(self._click_element_node_impl(element_node))

			# Check for validation errors
			if isinstance(click_metadata, dict) and 'validation_error' in click_metadata:
				self.logger.info(f'{click_metadata["validation_error"]}')
				return click_metadata

			# Build success message for non-download clicks
			if 'download' not in (click_metadata or {}):
				msg = f'Clicked button {element_node.node_name}: {element_node.get_all_children_text(max_depth=2)}'
				self.logger.debug(f'🖱️ {msg}')
			self.logger.debug(f'Element xpath: {element_node.xpath}')

			return click_metadata

		except Exception:
			raise