async def on_ClickCoordinateEvent(self, event: ClickCoordinateEvent) -> dict | None:
		"""Handle click at coordinates with CDP. Automatically waits for file downloads if triggered."""
		try:
			# Check if session is alive before attempting any operations
			if not self.browser_session.agent_focus_target_id:
				error_msg = 'Cannot execute click: browser session is corrupted (target_id=None). Session may have crashed.'
				self.logger.error(f'{error_msg}')
				raise BrowserError(error_msg)

			# If force=True, skip safety checks and click directly (with download detection)
			if event.force:
				self.logger.debug(f'Force clicking at coordinates ({event.coordinate_x}, {event.coordinate_y})')
				return await self._execute_click_with_download_detection(
					self._click_on_coordinate(event.coordinate_x, event.coordinate_y, force=True)
				)

			# Get element at coordinates for safety checks
			element_node = await self.browser_session.get_dom_element_at_coordinates(event.coordinate_x, event.coordinate_y)
			if element_node is None:
				# No element found, click directly (with download detection)
				self.logger.debug(
					f'No element found at coordinates ({event.coordinate_x}, {event.coordinate_y}), proceeding with click anyway'
				)
				return await self._execute_click_with_download_detection(
					self._click_on_coordinate(event.coordinate_x, event.coordinate_y, force=False)
				)

			# Safety check: file input
			if self.browser_session.is_file_input(element_node):
				msg = f'Cannot click at ({event.coordinate_x}, {event.coordinate_y}) - element is a file input. To upload files please use upload_file action'
				self.logger.info(f'{msg}')
				return {'validation_error': msg}

			# Safety check: select element
			tag_name = element_node.tag_name.lower() if element_node.tag_name else ''
			if tag_name == 'select':
				msg = f'Cannot click at ({event.coordinate_x}, {event.coordinate_y}) - element is a <select>. Use dropdown_options action instead.'
				self.logger.info(f'{msg}')
				return {'validation_error': msg}

			# Safety check: print-related elements
			is_print_element = self._is_print_related_element(element_node)
			if is_print_element:
				self.logger.info(
					f'🖨️ Detected print button at ({event.coordinate_x}, {event.coordinate_y}), generating PDF directly instead of opening dialog...'
				)
				click_metadata = await self._handle_print_button_click(element_node)
				if click_metadata and click_metadata.get('pdf_generated'):
					msg = f'Generated PDF: {click_metadata.get("path")}'
					self.logger.info(f'💾 {msg}')
					return click_metadata
				else:
					self.logger.warning('⚠️ PDF generation failed, falling back to regular click')

			# All safety checks passed, click at coordinates (with download detection)
			return await self._execute_click_with_download_detection(
				self._click_on_coordinate(event.coordinate_x, event.coordinate_y, force=False)
			)

		except Exception:
			raise