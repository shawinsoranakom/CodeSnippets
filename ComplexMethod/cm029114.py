async def _construct_enhanced_node(
			node: Node,
			html_frames: list[EnhancedDOMTreeNode] | None,
			total_frame_offset: DOMRect | None,
			all_frames: dict | None,
		) -> EnhancedDOMTreeNode:
			"""
			Recursively construct enhanced DOM tree nodes.

			Args:
				node: The DOM node to construct
				html_frames: List of HTML frame nodes encountered so far
				total_frame_offset: Accumulated coordinate translation from parent iframes (includes scroll corrections)
				all_frames: Pre-fetched frame hierarchy to avoid redundant CDP calls
			"""

			# Initialize lists if not provided
			if html_frames is None:
				html_frames = []

			# to get rid of the pointer references
			if total_frame_offset is None:
				total_frame_offset = DOMRect(x=0.0, y=0.0, width=0.0, height=0.0)
			else:
				total_frame_offset = DOMRect(
					total_frame_offset.x, total_frame_offset.y, total_frame_offset.width, total_frame_offset.height
				)

			# memoize the mf (I don't know if some nodes are duplicated)
			if node['nodeId'] in enhanced_dom_tree_node_lookup:
				return enhanced_dom_tree_node_lookup[node['nodeId']]

			ax_node = ax_tree_lookup.get(node['backendNodeId'])
			if ax_node:
				enhanced_ax_node = self._build_enhanced_ax_node(ax_node)
			else:
				enhanced_ax_node = None

			# To make attributes more readable
			attributes: dict[str, str] | None = None
			if 'attributes' in node and node['attributes']:
				attributes = {}
				for i in range(0, len(node['attributes']), 2):
					attributes[node['attributes'][i]] = node['attributes'][i + 1]

			shadow_root_type = None
			if 'shadowRootType' in node and node['shadowRootType']:
				try:
					shadow_root_type = node['shadowRootType']
				except ValueError:
					pass

			# Get snapshot data and calculate absolute position
			snapshot_data = snapshot_lookup.get(node['backendNodeId'], None)

			# DIAGNOSTIC: Log when interactive elements don't have snapshot data
			if not snapshot_data and node['nodeName'].upper() in ['INPUT', 'BUTTON', 'SELECT', 'TEXTAREA', 'A']:
				parent_has_shadow = False
				parent_info = ''
				if 'parentId' in node and node['parentId'] in enhanced_dom_tree_node_lookup:
					parent = enhanced_dom_tree_node_lookup[node['parentId']]
					if parent.shadow_root_type:
						parent_has_shadow = True
						parent_info = f'parent={parent.tag_name}(shadow={parent.shadow_root_type})'
				attr_str = ''
				if 'attributes' in node and node['attributes']:
					attrs_dict = {node['attributes'][i]: node['attributes'][i + 1] for i in range(0, len(node['attributes']), 2)}
					attr_str = f'name={attrs_dict.get("name", "N/A")} id={attrs_dict.get("id", "N/A")}'
				self.logger.debug(
					f'🔍 NO SNAPSHOT DATA for <{node["nodeName"]}> backendNodeId={node["backendNodeId"]} '
					f'{attr_str} {parent_info} (snapshot_lookup has {len(snapshot_lookup)} entries)'
				)

			absolute_position = None
			if snapshot_data and snapshot_data.bounds:
				absolute_position = DOMRect(
					x=snapshot_data.bounds.x + total_frame_offset.x,
					y=snapshot_data.bounds.y + total_frame_offset.y,
					width=snapshot_data.bounds.width,
					height=snapshot_data.bounds.height,
				)

			try:
				session = await self.browser_session.get_or_create_cdp_session(target_id, focus=False)
				session_id = session.session_id
			except ValueError:
				# Target may have detached during DOM construction
				session_id = None

			dom_tree_node = EnhancedDOMTreeNode(
				node_id=node['nodeId'],
				backend_node_id=node['backendNodeId'],
				node_type=NodeType(node['nodeType']),
				node_name=node['nodeName'],
				node_value=node['nodeValue'],
				attributes=attributes or {},
				is_scrollable=node.get('isScrollable', None),
				frame_id=node.get('frameId', None),
				session_id=session_id,
				target_id=target_id,
				content_document=None,
				shadow_root_type=shadow_root_type,
				shadow_roots=None,
				parent_node=None,
				children_nodes=None,
				ax_node=enhanced_ax_node,
				snapshot_node=snapshot_data,
				is_visible=None,
				has_js_click_listener=node['backendNodeId'] in js_click_listener_backend_ids,
				absolute_position=absolute_position,
			)

			enhanced_dom_tree_node_lookup[node['nodeId']] = dom_tree_node

			if 'parentId' in node and node['parentId']:
				dom_tree_node.parent_node = enhanced_dom_tree_node_lookup[
					node['parentId']
				]  # parents should always be in the lookup

			# Check if this is an HTML frame node and add it to the list
			updated_html_frames = html_frames.copy()
			if node['nodeType'] == NodeType.ELEMENT_NODE.value and node['nodeName'] == 'HTML' and node.get('frameId') is not None:
				updated_html_frames.append(dom_tree_node)

				# and adjust the total frame offset by scroll
				if snapshot_data and snapshot_data.scrollRects:
					total_frame_offset.x -= snapshot_data.scrollRects.x
					total_frame_offset.y -= snapshot_data.scrollRects.y
					# DEBUG: Log iframe scroll information
					self.logger.debug(
						f'🔍 DEBUG: HTML frame scroll - scrollY={snapshot_data.scrollRects.y}, scrollX={snapshot_data.scrollRects.x}, frameId={node.get("frameId")}, nodeId={node["nodeId"]}'
					)

			# Calculate new iframe offset for content documents, accounting for iframe scroll
			if (
				(node['nodeName'].upper() == 'IFRAME' or node['nodeName'].upper() == 'FRAME')
				and snapshot_data
				and snapshot_data.bounds
			):
				if snapshot_data.bounds:
					updated_html_frames.append(dom_tree_node)

					total_frame_offset.x += snapshot_data.bounds.x
					total_frame_offset.y += snapshot_data.bounds.y

			if 'contentDocument' in node and node['contentDocument']:
				dom_tree_node.content_document = await _construct_enhanced_node(
					node['contentDocument'], updated_html_frames, total_frame_offset, all_frames
				)
				dom_tree_node.content_document.parent_node = dom_tree_node
				# forcefully set the parent node to the content document node (helps traverse the tree)

			if 'shadowRoots' in node and node['shadowRoots']:
				dom_tree_node.shadow_roots = []
				for shadow_root in node['shadowRoots']:
					shadow_root_node = await _construct_enhanced_node(
						shadow_root, updated_html_frames, total_frame_offset, all_frames
					)
					# forcefully set the parent node to the shadow root node (helps traverse the tree)
					shadow_root_node.parent_node = dom_tree_node
					dom_tree_node.shadow_roots.append(shadow_root_node)

			if 'children' in node and node['children']:
				dom_tree_node.children_nodes = []
				# Build set of shadow root node IDs to filter them out from children
				shadow_root_node_ids = set()
				if 'shadowRoots' in node and node['shadowRoots']:
					for shadow_root in node['shadowRoots']:
						shadow_root_node_ids.add(shadow_root['nodeId'])

				for child in node['children']:
					# Skip shadow roots - they should only be in shadow_roots list
					if child['nodeId'] in shadow_root_node_ids:
						continue
					dom_tree_node.children_nodes.append(
						await _construct_enhanced_node(child, updated_html_frames, total_frame_offset, all_frames)
					)

			# Set visibility using the collected HTML frames and viewport threshold
			dom_tree_node.is_visible = self.is_element_visible_according_to_all_parents(
				dom_tree_node, updated_html_frames, self.viewport_threshold
			)

			# DEBUG: Log visibility info for form elements in iframes
			if dom_tree_node.tag_name and dom_tree_node.tag_name.upper() in ['INPUT', 'SELECT', 'TEXTAREA', 'LABEL']:
				attrs = dom_tree_node.attributes or {}
				elem_id = attrs.get('id', '')
				elem_name = attrs.get('name', '')
				if (
					'city' in elem_id.lower()
					or 'city' in elem_name.lower()
					or 'state' in elem_id.lower()
					or 'state' in elem_name.lower()
					or 'zip' in elem_id.lower()
					or 'zip' in elem_name.lower()
				):
					self.logger.debug(
						f"🔍 DEBUG: Form element {dom_tree_node.tag_name} id='{elem_id}' name='{elem_name}' - visible={dom_tree_node.is_visible}, bounds={dom_tree_node.snapshot_node.bounds if dom_tree_node.snapshot_node else 'NO_SNAPSHOT'}"
					)

			# handle cross origin iframe (just recursively call the main function with the proper target if it exists in iframes)
			# only do this if the iframe is visible (otherwise it's not worth it)

			if (
				# TODO: hacky way to disable cross origin iframes for now
				self.cross_origin_iframes and node['nodeName'].upper() == 'IFRAME' and node.get('contentDocument', None) is None
			):  # None meaning there is no content
				# Check iframe depth to prevent infinite recursion
				if iframe_depth >= self.max_iframe_depth:
					self.logger.debug(
						f'Skipping iframe at depth {iframe_depth} to prevent infinite recursion (max depth: {self.max_iframe_depth})'
					)
				else:
					# Check if iframe is visible and large enough (>= 50px in both dimensions)
					should_process_iframe = False

					# First check if the iframe element itself is visible
					if dom_tree_node.is_visible:
						# Check iframe dimensions
						if dom_tree_node.snapshot_node and dom_tree_node.snapshot_node.bounds:
							bounds = dom_tree_node.snapshot_node.bounds
							width = bounds.width
							height = bounds.height

							# Only process if iframe is at least 50px in both dimensions
							if width >= 50 and height >= 50:
								should_process_iframe = True
								self.logger.debug(f'Processing cross-origin iframe: visible=True, width={width}, height={height}')
							else:
								self.logger.debug(
									f'Skipping small cross-origin iframe: width={width}, height={height} (needs >= 50px)'
								)
						else:
							self.logger.debug('Skipping cross-origin iframe: no bounds available')
					else:
						self.logger.debug('Skipping invisible cross-origin iframe')

					if should_process_iframe:
						# Lazy fetch all_frames only when actually needed (for cross-origin iframes)
						if all_frames is None:
							all_frames, _ = await self.browser_session.get_all_frames()

						# Use pre-fetched all_frames to find the iframe's target (no redundant CDP call)
						frame_id = node.get('frameId', None)

						# Fallback: if frameId is missing or not in all_frames, try URL matching via
						# the src attribute. This handles dynamically-injected iframes (e.g. HubSpot
						# popups, chat widgets) where Chrome hasn't yet registered the frameId in the
						# frame tree at DOM-snapshot time.
						if (not frame_id or frame_id not in all_frames) and attributes:
							src = attributes.get('src', '')
							if src:
								src_base = src.split('?')[0].rstrip('/')
								for fid, finfo in all_frames.items():
									frame_url = finfo.get('url', '').split('?')[0].rstrip('/')
									if frame_url and frame_url == src_base:
										frame_id = fid
										self.logger.debug(f'Matched cross-origin iframe by src URL: {src!r} -> frameId={fid}')
										break

						iframe_document_target = None
						if frame_id:
							frame_info = all_frames.get(frame_id)
							if frame_info and frame_info.get('frameTargetId'):
								iframe_target_id = frame_info['frameTargetId']
								# Use frameTargetId directly from all_frames — get_all_frames() already
								# validated connectivity. Do NOT gate on session_manager.get_target():
								# there is a race where _target_sessions is set (inside the lock in
								# _handle_target_attached) before _targets is populated (outside the
								# lock), so get_target() can transiently return None for a live target.
								iframe_target = self.browser_session.session_manager.get_target(iframe_target_id)
								iframe_document_target = {
									'targetId': iframe_target_id,
									'url': iframe_target.url if iframe_target else frame_info.get('url', ''),
									'title': iframe_target.title if iframe_target else frame_info.get('title', ''),
									'type': iframe_target.target_type if iframe_target else 'iframe',
								}

						# if target actually exists in one of the frames, just recursively build the dom tree for it
						if iframe_document_target:
							self.logger.debug(
								f'Getting content document for iframe {node.get("frameId", None)} at depth {iframe_depth + 1}'
							)
							try:
								content_document, _ = await self.get_dom_tree(
									target_id=iframe_document_target['targetId'],
									all_frames=all_frames,
									# Current config: if the cross origin iframe is AT ALL visible, include everything inside it
									initial_total_frame_offset=total_frame_offset,
									iframe_depth=iframe_depth + 1,
								)
								dom_tree_node.content_document = content_document
								dom_tree_node.content_document.parent_node = dom_tree_node
							except Exception as e:
								self.logger.debug(f'Failed to get DOM tree for cross-origin iframe {frame_id}: {e}')

			return dom_tree_node