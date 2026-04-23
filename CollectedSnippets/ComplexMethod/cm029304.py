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