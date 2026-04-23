async def get_element_coordinates(self, backend_node_id: int, cdp_session: CDPSession) -> DOMRect | None:
		"""Get element coordinates for a backend node ID using multiple methods.

		This method tries DOM.getContentQuads first, then falls back to DOM.getBoxModel,
		and finally uses JavaScript getBoundingClientRect as a last resort.

		Args:
			backend_node_id: The backend node ID to get coordinates for
			cdp_session: The CDP session to use

		Returns:
			DOMRect with coordinates or None if element not found/no bounds
		"""
		session_id = cdp_session.session_id
		quads = []

		# Method 1: Try DOM.getContentQuads first (best for inline elements and complex layouts)
		try:
			content_quads_result = await cdp_session.cdp_client.send.DOM.getContentQuads(
				params={'backendNodeId': backend_node_id}, session_id=session_id
			)
			if 'quads' in content_quads_result and content_quads_result['quads']:
				quads = content_quads_result['quads']
				self.logger.debug(f'Got {len(quads)} quads from DOM.getContentQuads')
			else:
				self.logger.debug(f'No quads found from DOM.getContentQuads {content_quads_result}')
		except Exception as e:
			self.logger.debug(f'DOM.getContentQuads failed: {e}')

		# Method 2: Fall back to DOM.getBoxModel
		if not quads:
			try:
				box_model = await cdp_session.cdp_client.send.DOM.getBoxModel(
					params={'backendNodeId': backend_node_id}, session_id=session_id
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
						self.logger.debug('Got quad from DOM.getBoxModel')
			except Exception as e:
				self.logger.debug(f'DOM.getBoxModel failed: {e}')

		# Method 3: Fall back to JavaScript getBoundingClientRect
		if not quads:
			try:
				result = await cdp_session.cdp_client.send.DOM.resolveNode(
					params={'backendNodeId': backend_node_id},
					session_id=session_id,
				)
				if 'object' in result and 'objectId' in result['object']:
					object_id = result['object']['objectId']
					js_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'objectId': object_id,
							'functionDeclaration': """
							function() {
								const rect = this.getBoundingClientRect();
								return {
									x: rect.x,
									y: rect.y,
									width: rect.width,
									height: rect.height
								};
							}
							""",
							'returnByValue': True,
						},
						session_id=session_id,
					)
					if 'result' in js_result and 'value' in js_result['result']:
						rect_data = js_result['result']['value']
						if rect_data['width'] > 0 and rect_data['height'] > 0:
							return DOMRect(
								x=rect_data['x'], y=rect_data['y'], width=rect_data['width'], height=rect_data['height']
							)
			except Exception as e:
				self.logger.debug(f'JavaScript getBoundingClientRect failed: {e}')

		# Convert quads to bounding rectangle if we have them
		if quads:
			# Use the first quad (most relevant for the element)
			quad = quads[0]
			if len(quad) >= 8:
				# Calculate bounding rect from quad points
				x_coords = [quad[i] for i in range(0, 8, 2)]
				y_coords = [quad[i] for i in range(1, 8, 2)]

				min_x = min(x_coords)
				min_y = min(y_coords)
				max_x = max(x_coords)
				max_y = max(y_coords)

				width = max_x - min_x
				height = max_y - min_y

				if width > 0 and height > 0:
					return DOMRect(x=min_x, y=min_y, width=width, height=height)

		return None