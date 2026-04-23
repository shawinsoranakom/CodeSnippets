async def _click_element_node_impl(self, element_node) -> dict | None:
		"""
		Click an element using pure CDP with multiple fallback methods for getting element geometry.

		Args:
			element_node: The DOM element to click
		"""

		try:
			# Check if element is a file input or select dropdown - these should not be clicked
			tag_name = element_node.tag_name.lower() if element_node.tag_name else ''
			element_type = element_node.attributes.get('type', '').lower() if element_node.attributes else ''

			if tag_name == 'select':
				msg = f'Cannot click on <select> elements. Use dropdown_options(index={element_node.backend_node_id}) action instead.'
				# Return error dict instead of raising to avoid ERROR logs
				return {'validation_error': msg}

			if tag_name == 'input' and element_type == 'file':
				msg = f'Cannot click on file input element (index={element_node.backend_node_id}). File uploads must be handled using upload_file_to_element action.'
				# Return error dict instead of raising to avoid ERROR logs
				return {'validation_error': msg}

			# Get CDP client
			cdp_session = await self.browser_session.cdp_client_for_node(element_node)

			# Get the correct session ID for the element's frame
			session_id = cdp_session.session_id

			# Get element bounds
			backend_node_id = element_node.backend_node_id

			# For checkbox/radio: capture pre-click state to verify toggle worked
			is_toggle_element = tag_name == 'input' and element_type in ('checkbox', 'radio')
			pre_click_checked: bool | None = None
			checkbox_object_id: str | None = None
			if is_toggle_element and backend_node_id:
				try:
					resolve_res = await cdp_session.cdp_client.send.DOM.resolveNode(
						params={'backendNodeId': backend_node_id}, session_id=session_id
					)
					obj_info = resolve_res.get('object', {})
					checkbox_object_id = obj_info.get('objectId') if obj_info else None
					if not checkbox_object_id:
						raise Exception('Failed to resolve checkbox element objectId')
					state_res = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': 'function() { return this.checked; }',
							'objectId': checkbox_object_id,
							'returnByValue': True,
						},
						session_id=session_id,
					)
					pre_click_checked = state_res.get('result', {}).get('value')
					self.logger.debug(f'Checkbox pre-click state: checked={pre_click_checked}')
				except Exception as e:
					self.logger.debug(f'Could not capture pre-click checkbox state: {e}')

			# Get viewport dimensions for visibility checks
			layout_metrics = await cdp_session.cdp_client.send.Page.getLayoutMetrics(session_id=session_id)
			viewport_width = layout_metrics['layoutViewport']['clientWidth']
			viewport_height = layout_metrics['layoutViewport']['clientHeight']

			# Scroll element into view FIRST before getting coordinates
			try:
				await cdp_session.cdp_client.send.DOM.scrollIntoViewIfNeeded(
					params={'backendNodeId': backend_node_id}, session_id=session_id
				)
				await asyncio.sleep(0.05)  # Wait for scroll to complete
				self.logger.debug('Scrolled element into view before getting coordinates')
			except Exception as e:
				self.logger.debug(f'Failed to scroll element into view: {e}')

			# Get element coordinates using the unified method AFTER scrolling
			element_rect = await self.browser_session.get_element_coordinates(backend_node_id, cdp_session)

			# Convert rect to quads format if we got coordinates
			quads = []
			if element_rect:
				# Convert DOMRect to quad format
				x, y, w, h = element_rect.x, element_rect.y, element_rect.width, element_rect.height
				quads = [
					[
						x,
						y,  # top-left
						x + w,
						y,  # top-right
						x + w,
						y + h,  # bottom-right
						x,
						y + h,  # bottom-left
					]
				]
				self.logger.debug(
					f'Got coordinates from unified method: {element_rect.x}, {element_rect.y}, {element_rect.width}x{element_rect.height}'
				)

			# If we still don't have quads, fall back to JS click
			if not quads:
				self.logger.warning('Could not get element geometry from any method, falling back to JavaScript click')
				try:
					result = await cdp_session.cdp_client.send.DOM.resolveNode(
						params={'backendNodeId': backend_node_id},
						session_id=session_id,
					)
					assert 'object' in result and 'objectId' in result['object'], (
						'Failed to find DOM element based on backendNodeId, maybe page content changed?'
					)
					object_id = result['object']['objectId']

					await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': 'function() { this.click(); }',
							'objectId': object_id,
						},
						session_id=session_id,
					)
					await asyncio.sleep(0.05)
					# Navigation is handled by BrowserSession via events
					return None
				except Exception as js_e:
					self.logger.warning(f'CDP JavaScript click also failed: {js_e}')
					if 'No node with given id found' in str(js_e):
						raise Exception('Element with given id not found')
					else:
						raise Exception(f'Failed to click element: {js_e}')

			# Find the largest visible quad within the viewport
			best_quad = None
			best_area = 0

			for quad in quads:
				if len(quad) < 8:
					continue

				# Calculate quad bounds
				xs = [quad[i] for i in range(0, 8, 2)]
				ys = [quad[i] for i in range(1, 8, 2)]
				min_x, max_x = min(xs), max(xs)
				min_y, max_y = min(ys), max(ys)

				# Check if quad intersects with viewport
				if max_x < 0 or max_y < 0 or min_x > viewport_width or min_y > viewport_height:
					continue  # Quad is completely outside viewport

				# Calculate visible area (intersection with viewport)
				visible_min_x = max(0, min_x)
				visible_max_x = min(viewport_width, max_x)
				visible_min_y = max(0, min_y)
				visible_max_y = min(viewport_height, max_y)

				visible_width = visible_max_x - visible_min_x
				visible_height = visible_max_y - visible_min_y
				visible_area = visible_width * visible_height

				if visible_area > best_area:
					best_area = visible_area
					best_quad = quad

			if not best_quad:
				# No visible quad found, use the first quad anyway
				best_quad = quads[0]
				self.logger.warning('No visible quad found, using first quad')

			# Calculate center point of the best quad
			center_x = sum(best_quad[i] for i in range(0, 8, 2)) / 4
			center_y = sum(best_quad[i] for i in range(1, 8, 2)) / 4

			# Ensure click point is within viewport bounds
			center_x = max(0, min(viewport_width - 1, center_x))
			center_y = max(0, min(viewport_height - 1, center_y))

			# Check for occlusion before attempting CDP click
			is_occluded = await self._check_element_occlusion(backend_node_id, center_x, center_y, cdp_session)

			if is_occluded:
				self.logger.debug('🚫 Element is occluded, falling back to JavaScript click')
				try:
					result = await cdp_session.cdp_client.send.DOM.resolveNode(
						params={'backendNodeId': backend_node_id},
						session_id=session_id,
					)
					assert 'object' in result and 'objectId' in result['object'], (
						'Failed to find DOM element based on backendNodeId'
					)
					object_id = result['object']['objectId']

					await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': 'function() { this.click(); }',
							'objectId': object_id,
						},
						session_id=session_id,
					)
					await asyncio.sleep(0.05)
					return None
				except Exception as js_e:
					self.logger.error(f'JavaScript click fallback failed: {js_e}')
					raise Exception(f'Failed to click occluded element: {js_e}')

			# Perform the click using CDP (element is not occluded)
			try:
				self.logger.debug(f'👆 Dragging mouse over element before clicking x: {center_x}px y: {center_y}px ...')
				# Move mouse to element
				await cdp_session.cdp_client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mouseMoved',
						'x': center_x,
						'y': center_y,
					},
					session_id=session_id,
				)
				await asyncio.sleep(0.05)

				# Mouse down
				self.logger.debug(f'👆🏾 Clicking x: {center_x}px y: {center_y}px ...')
				try:
					await asyncio.wait_for(
						cdp_session.cdp_client.send.Input.dispatchMouseEvent(
							params={
								'type': 'mousePressed',
								'x': center_x,
								'y': center_y,
								'button': 'left',
								'clickCount': 1,
							},
							session_id=session_id,
						),
						timeout=3.0,  # 3 second timeout for mousePressed
					)
					await asyncio.sleep(0.08)
				except TimeoutError:
					self.logger.debug('⏱️ Mouse down timed out (likely due to dialog), continuing...')
					# Don't sleep if we timed out

				# Mouse up
				try:
					await asyncio.wait_for(
						cdp_session.cdp_client.send.Input.dispatchMouseEvent(
							params={
								'type': 'mouseReleased',
								'x': center_x,
								'y': center_y,
								'button': 'left',
								'clickCount': 1,
							},
							session_id=session_id,
						),
						timeout=5.0,  # 5 second timeout for mouseReleased
					)
				except TimeoutError:
					self.logger.debug('⏱️ Mouse up timed out (possibly due to lag or dialog popup), continuing...')

				self.logger.debug('🖱️ Clicked successfully using x,y coordinates')

				# For checkbox/radio: verify state toggled, fall back to JS element.click() if not
				if is_toggle_element and pre_click_checked is not None and checkbox_object_id:
					try:
						await asyncio.sleep(0.05)
						state_res = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
							params={
								'functionDeclaration': 'function() { return this.checked; }',
								'objectId': checkbox_object_id,
								'returnByValue': True,
							},
							session_id=session_id,
						)
						post_click_checked = state_res.get('result', {}).get('value')
						if post_click_checked == pre_click_checked:
							# CDP mouse events didn't toggle the checkbox — try JS element.click()
							self.logger.debug(
								f'Checkbox state unchanged after CDP click (checked={pre_click_checked}), using JS fallback'
							)
							await cdp_session.cdp_client.send.Runtime.callFunctionOn(
								params={'functionDeclaration': 'function() { this.click(); }', 'objectId': checkbox_object_id},
								session_id=session_id,
							)
							await asyncio.sleep(0.05)
							final_res = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
								params={
									'functionDeclaration': 'function() { return this.checked; }',
									'objectId': checkbox_object_id,
									'returnByValue': True,
								},
								session_id=session_id,
							)
							post_click_checked = final_res.get('result', {}).get('value')
						self.logger.debug(f'Checkbox post-click state: checked={post_click_checked}')
						return {'click_x': center_x, 'click_y': center_y, 'checked': post_click_checked}
					except Exception as e:
						self.logger.debug(f'Checkbox state verification failed (non-critical): {e}')

				# Return coordinates as dict for metadata
				return {'click_x': center_x, 'click_y': center_y}

			except Exception as e:
				self.logger.warning(f'CDP click failed: {type(e).__name__}: {e}')
				# Fall back to JavaScript click via CDP
				try:
					result = await cdp_session.cdp_client.send.DOM.resolveNode(
						params={'backendNodeId': backend_node_id},
						session_id=session_id,
					)
					assert 'object' in result and 'objectId' in result['object'], (
						'Failed to find DOM element based on backendNodeId, maybe page content changed?'
					)
					object_id = result['object']['objectId']

					await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': 'function() { this.click(); }',
							'objectId': object_id,
						},
						session_id=session_id,
					)

					# Small delay for dialog dismissal
					await asyncio.sleep(0.1)

					return None
				except Exception as js_e:
					self.logger.warning(f'CDP JavaScript click also failed: {js_e}')
					raise Exception(f'Failed to click element: {e}')
			finally:
				# Always re-focus back to original top-level page session context in case click opened a new tab/popup/window/dialog/etc.
				# Use timeout to prevent hanging if dialog is blocking
				try:
					cdp_session = await asyncio.wait_for(self.browser_session.get_or_create_cdp_session(focus=True), timeout=3.0)
					await asyncio.wait_for(
						cdp_session.cdp_client.send.Runtime.runIfWaitingForDebugger(session_id=cdp_session.session_id),
						timeout=2.0,
					)
				except TimeoutError:
					self.logger.debug('⏱️ Refocus after click timed out (page may be blocked by dialog). Continuing...')
				except Exception as e:
					self.logger.debug(f'⚠️ Refocus error (non-critical): {type(e).__name__}: {e}')

		except URLNotAllowedError as e:
			raise e
		except BrowserError as e:
			raise e
		except Exception as e:
			# Extract key element info for error message
			element_info = f'<{element_node.tag_name or "unknown"}'
			if element_node.backend_node_id:
				element_info += f' index={element_node.backend_node_id}'
			element_info += '>'

			# Create helpful error message based on context
			error_detail = f'Failed to click element {element_info}. The element may not be interactable or visible.'

			# Add hint if element has index (common in code-use mode)
			if element_node.backend_node_id:
				error_detail += f' If the page changed after navigation/interaction, the index [{element_node.backend_node_id}] may be stale. Get fresh browser state before retrying.'

			raise BrowserError(
				message=f'Failed to click element: {str(e)}',
				long_term_memory=error_detail,
			)