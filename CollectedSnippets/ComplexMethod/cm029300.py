async def get_all_frames(self) -> tuple[dict[str, dict], dict[str, str]]:
		"""Get a complete frame hierarchy from all browser targets.

		Returns:
			Tuple of (all_frames, target_sessions) where:
			- all_frames: dict mapping frame_id -> frame info dict with all metadata
			- target_sessions: dict mapping target_id -> session_id for active sessions
		"""
		all_frames = {}  # frame_id -> FrameInfo dict
		target_sessions = {}  # target_id -> session_id (keep sessions alive during collection)

		# Check if cross-origin iframe support is enabled
		include_cross_origin = self.browser_profile.cross_origin_iframes

		# Get all targets - only include iframes if cross-origin support is enabled
		targets = await self._cdp_get_all_pages(
			include_http=True,
			include_about=True,
			include_pages=True,
			include_iframes=include_cross_origin,  # Only include iframe targets if flag is set
			include_workers=False,
			include_chrome=False,
			include_chrome_extensions=False,
			include_chrome_error=include_cross_origin,  # Only include error pages if cross-origin is enabled
		)
		all_targets = targets

		# First pass: collect frame trees from ALL targets
		for target in all_targets:
			target_id = target['targetId']

			# Skip iframe targets if cross-origin support is disabled
			if not include_cross_origin and target.get('type') == 'iframe':
				continue

			# When cross-origin support is disabled, only process the current target
			if not include_cross_origin:
				# Only process the current focus target
				if self.agent_focus_target_id and target_id != self.agent_focus_target_id:
					continue
				# Use the existing agent_focus target's session - use safe API with focus=False
				try:
					cdp_session = await self.get_or_create_cdp_session(self.agent_focus_target_id, focus=False)
				except ValueError:
					continue  # Skip if no session available
			else:
				# Get cached session for this target (don't change focus - iterating frames)
				try:
					cdp_session = await self.get_or_create_cdp_session(target_id, focus=False)
				except ValueError:
					continue  # Target may have detached between discovery and session creation

			if cdp_session:
				target_sessions[target_id] = cdp_session.session_id

				try:
					# Try to get frame tree (not all target types support this)
					frame_tree_result = await cdp_session.cdp_client.send.Page.getFrameTree(session_id=cdp_session.session_id)

					# Process the frame tree recursively
					def process_frame_tree(node, parent_frame_id=None):
						"""Recursively process frame tree and add to all_frames."""
						frame = node.get('frame', {})
						current_frame_id = frame.get('id')

						if current_frame_id:
							# For iframe targets, check if the frame has a parentId field
							# This indicates it's an OOPIF with a parent in another target
							actual_parent_id = frame.get('parentId') or parent_frame_id

							# Create frame info with all CDP response data plus our additions
							frame_info = {
								**frame,  # Include all original frame data: id, url, parentId, etc.
								'frameTargetId': target_id,  # Target that can access this frame
								'parentFrameId': actual_parent_id,  # Use parentId from frame if available
								'childFrameIds': [],  # Will be populated below
								'isCrossOrigin': False,  # Will be determined based on context
								'isValidTarget': self._is_valid_target(
									target,
									include_http=True,
									include_about=True,
									include_pages=True,
									include_iframes=True,
									include_workers=False,
									include_chrome=False,  # chrome://newtab, chrome://settings, etc. are not valid frames we can control (for sanity reasons)
									include_chrome_extensions=False,  # chrome-extension://
									include_chrome_error=False,  # chrome-error://  (e.g. when iframes fail to load or are blocked by uBlock Origin)
								),
							}

							# Check if frame is cross-origin based on crossOriginIsolatedContextType
							cross_origin_type = frame.get('crossOriginIsolatedContextType')
							if cross_origin_type and cross_origin_type != 'NotIsolated':
								frame_info['isCrossOrigin'] = True

							# For iframe targets, the frame itself is likely cross-origin
							if target.get('type') == 'iframe':
								frame_info['isCrossOrigin'] = True

							# Skip cross-origin frames if support is disabled
							if not include_cross_origin and frame_info.get('isCrossOrigin'):
								return  # Skip this frame and its children

							# Add child frame IDs (note: OOPIFs won't appear here)
							child_frames = node.get('childFrames', [])
							for child in child_frames:
								child_frame = child.get('frame', {})
								child_frame_id = child_frame.get('id')
								if child_frame_id:
									frame_info['childFrameIds'].append(child_frame_id)

							# Store or merge frame info
							if current_frame_id in all_frames:
								# Frame already seen from another target, merge info
								existing = all_frames[current_frame_id]
								# If this is an iframe target, it has direct access to the frame
								if target.get('type') == 'iframe':
									existing['frameTargetId'] = target_id
									existing['isCrossOrigin'] = True
							else:
								all_frames[current_frame_id] = frame_info

							# Process child frames recursively (only if we're not skipping this frame)
							if include_cross_origin or not frame_info.get('isCrossOrigin'):
								for child in child_frames:
									process_frame_tree(child, current_frame_id)

					# Process the entire frame tree
					process_frame_tree(frame_tree_result.get('frameTree', {}))

				except Exception as e:
					# Target doesn't support Page domain or has no frames
					self.logger.debug(f'Failed to get frame tree for target {target_id}: {e}')

		# Second pass: populate backend node IDs and parent target IDs
		# Only do this if cross-origin support is enabled
		if include_cross_origin:
			await self._populate_frame_metadata(all_frames, target_sessions)

		return all_frames, target_sessions