async def drag_to(
		self,
		target: Union['Element', Position],
		source_position: Position | None = None,
		target_position: Position | None = None,
	) -> None:
		"""Drag this element to another element or position."""
		# Get source coordinates
		if source_position:
			source_x = source_position['x']
			source_y = source_position['y']
		else:
			source_box = await self.get_bounding_box()
			if not source_box:
				raise RuntimeError('Source element is not visible')
			source_x = source_box['x'] + source_box['width'] / 2
			source_y = source_box['y'] + source_box['height'] / 2

		# Get target coordinates
		if isinstance(target, dict) and 'x' in target and 'y' in target:
			target_x = target['x']
			target_y = target['y']
		else:
			if target_position:
				target_box = await target.get_bounding_box()
				if not target_box:
					raise RuntimeError('Target element is not visible')
				target_x = target_box['x'] + target_position['x']
				target_y = target_box['y'] + target_position['y']
			else:
				target_box = await target.get_bounding_box()
				if not target_box:
					raise RuntimeError('Target element is not visible')
				target_x = target_box['x'] + target_box['width'] / 2
				target_y = target_box['y'] + target_box['height'] / 2

		# Perform drag operation
		await self._client.send.Input.dispatchMouseEvent(
			{'type': 'mousePressed', 'x': source_x, 'y': source_y, 'button': 'left'},
			session_id=self._session_id,
		)

		await self._client.send.Input.dispatchMouseEvent(
			{'type': 'mouseMoved', 'x': target_x, 'y': target_y},
			session_id=self._session_id,
		)

		await self._client.send.Input.dispatchMouseEvent(
			{'type': 'mouseReleased', 'x': target_x, 'y': target_y, 'button': 'left'},
			session_id=self._session_id,
		)