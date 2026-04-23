async def click(
		self,
		button: 'MouseButton' = 'left',
		click_count: int = 1,
		modifiers: list[ModifierType] | None = None,
	) -> None:
		"""Click the element using the advanced watchdog implementation."""

		try:
			# Get viewport dimensions for visibility checks
			layout_metrics = await self._client.send.Page.getLayoutMetrics(session_id=self._session_id)
			viewport_width = layout_metrics['layoutViewport']['clientWidth']
			viewport_height = layout_metrics['layoutViewport']['clientHeight']

			# Try multiple methods to get element geometry
			quads = []

			# Method 1: Try DOM.getContentQuads first (best for inline elements and complex layouts)
			try:
				content_quads_result = await self._client.send.DOM.getContentQuads(
					params={'backendNodeId': self._backend_node_id}, session_id=self._session_id
				)
				if 'quads' in content_quads_result and content_quads_result['quads']:
					quads = content_quads_result['quads']
			except Exception:
				pass

			# Method 2: Fall back to DOM.getBoxModel
			if not quads:
				try:
					box_model = await self._client.send.DOM.getBoxModel(
						params={'backendNodeId': self._backend_node_id}, session_id=self._session_id
					)
					if 'model' in box_model and 'content' in box_model['model']:
						content_quad = box_model['model']['content']
						if len(content_quad) >= 8:
							# Convert box model format to quad format
							quads = [
								[
									content_quad[0],
									content_quad[1],  # x1, y1
									content_quad[2],
									content_quad[3],  # x2, y2
									content_quad[4],
									content_quad[5],  # x3, y3
									content_quad[6],
									content_quad[7],  # x4, y4
								]
							]
				except Exception:
					pass

			# Method 3: Fall back to JavaScript getBoundingClientRect
			if not quads:
				try:
					result = await self._client.send.DOM.resolveNode(
						params={'backendNodeId': self._backend_node_id}, session_id=self._session_id
					)
					if 'object' in result and 'objectId' in result['object']:
						object_id = result['object']['objectId']

						# Get bounding rect via JavaScript
						bounds_result = await self._client.send.Runtime.callFunctionOn(
							params={
								'functionDeclaration': """
									function() {
										const rect = this.getBoundingClientRect();
										return {
											x: rect.left,
											y: rect.top,
											width: rect.width,
											height: rect.height
										};
									}
								""",
								'objectId': object_id,
								'returnByValue': True,
							},
							session_id=self._session_id,
						)

						if 'result' in bounds_result and 'value' in bounds_result['result']:
							rect = bounds_result['result']['value']
							# Convert rect to quad format
							x, y, w, h = rect['x'], rect['y'], rect['width'], rect['height']
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
				except Exception:
					pass

			# If we still don't have quads, fall back to JS click
			if not quads:
				try:
					result = await self._client.send.DOM.resolveNode(
						params={'backendNodeId': self._backend_node_id}, session_id=self._session_id
					)
					if 'object' not in result or 'objectId' not in result['object']:
						raise Exception('Failed to find DOM element based on backendNodeId, maybe page content changed?')
					object_id = result['object']['objectId']

					await self._client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': 'function() { this.click(); }',
							'objectId': object_id,
						},
						session_id=self._session_id,
					)
					await asyncio.sleep(0.05)
					return
				except Exception as js_e:
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

			# Calculate center point of the best quad
			center_x = sum(best_quad[i] for i in range(0, 8, 2)) / 4
			center_y = sum(best_quad[i] for i in range(1, 8, 2)) / 4

			# Ensure click point is within viewport bounds
			center_x = max(0, min(viewport_width - 1, center_x))
			center_y = max(0, min(viewport_height - 1, center_y))

			# Scroll element into view
			try:
				await self._client.send.DOM.scrollIntoViewIfNeeded(
					params={'backendNodeId': self._backend_node_id}, session_id=self._session_id
				)
				await asyncio.sleep(0.05)  # Wait for scroll to complete
			except Exception:
				pass

			# Calculate modifier bitmask for CDP
			modifier_value = 0
			if modifiers:
				modifier_map = {'Alt': 1, 'Control': 2, 'Meta': 4, 'Shift': 8}
				for mod in modifiers:
					modifier_value |= modifier_map.get(mod, 0)

			# Perform the click using CDP
			try:
				# Move mouse to element
				await self._client.send.Input.dispatchMouseEvent(
					params={
						'type': 'mouseMoved',
						'x': center_x,
						'y': center_y,
					},
					session_id=self._session_id,
				)
				await asyncio.sleep(0.05)

				# Mouse down
				try:
					await asyncio.wait_for(
						self._client.send.Input.dispatchMouseEvent(
							params={
								'type': 'mousePressed',
								'x': center_x,
								'y': center_y,
								'button': button,
								'clickCount': click_count,
								'modifiers': modifier_value,
							},
							session_id=self._session_id,
						),
						timeout=1.0,  # 1 second timeout for mousePressed
					)
					await asyncio.sleep(0.08)
				except TimeoutError:
					pass  # Don't sleep if we timed out

				# Mouse up
				try:
					await asyncio.wait_for(
						self._client.send.Input.dispatchMouseEvent(
							params={
								'type': 'mouseReleased',
								'x': center_x,
								'y': center_y,
								'button': button,
								'clickCount': click_count,
								'modifiers': modifier_value,
							},
							session_id=self._session_id,
						),
						timeout=3.0,  # 3 second timeout for mouseReleased
					)
				except TimeoutError:
					pass

			except Exception as e:
				# Fall back to JavaScript click via CDP
				try:
					result = await self._client.send.DOM.resolveNode(
						params={'backendNodeId': self._backend_node_id}, session_id=self._session_id
					)
					if 'object' not in result or 'objectId' not in result['object']:
						raise Exception('Failed to find DOM element based on backendNodeId, maybe page content changed?')
					object_id = result['object']['objectId']

					await self._client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': 'function() { this.click(); }',
							'objectId': object_id,
						},
						session_id=self._session_id,
					)
					await asyncio.sleep(0.1)
					return
				except Exception as js_e:
					raise Exception(f'Failed to click element: {e}')

		except Exception as e:
			# Extract key element info for error message
			raise RuntimeError(f'Failed to click element: {e}')