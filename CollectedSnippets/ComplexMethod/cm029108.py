async def _get_all_trees(self, target_id: TargetID) -> TargetAllTrees:
		cdp_session = await self.browser_session.get_or_create_cdp_session(target_id=target_id, focus=False)

		# Wait for the page to be ready first
		try:
			ready_state = await cdp_session.cdp_client.send.Runtime.evaluate(
				params={'expression': 'document.readyState'}, session_id=cdp_session.session_id
			)
		except Exception as e:
			pass  # Page might not be ready yet
		# DEBUG: Log before capturing snapshot
		self.logger.debug(f'🔍 DEBUG: Capturing DOM snapshot for target {target_id}')

		# Get actual scroll positions for all iframes before capturing snapshot
		start_iframe_scroll = time.time()
		iframe_scroll_positions = {}
		try:
			scroll_result = await cdp_session.cdp_client.send.Runtime.evaluate(
				params={
					'expression': """
					(() => {
						const scrollData = {};
						const iframes = document.querySelectorAll('iframe');
						iframes.forEach((iframe, index) => {
							try {
								const doc = iframe.contentDocument || iframe.contentWindow.document;
								if (doc) {
									scrollData[index] = {
										scrollTop: doc.documentElement.scrollTop || doc.body.scrollTop || 0,
										scrollLeft: doc.documentElement.scrollLeft || doc.body.scrollLeft || 0
									};
								}
							} catch (e) {
								// Cross-origin iframe, can't access
							}
						});
						return scrollData;
					})()
					""",
					'returnByValue': True,
				},
				session_id=cdp_session.session_id,
			)
			if scroll_result and 'result' in scroll_result and 'value' in scroll_result['result']:
				iframe_scroll_positions = scroll_result['result']['value']
				for idx, scroll_data in iframe_scroll_positions.items():
					self.logger.debug(
						f'🔍 DEBUG: Iframe {idx} actual scroll position - scrollTop={scroll_data.get("scrollTop", 0)}, scrollLeft={scroll_data.get("scrollLeft", 0)}'
					)
		except Exception as e:
			self.logger.debug(f'Failed to get iframe scroll positions: {e}')
		iframe_scroll_ms = (time.time() - start_iframe_scroll) * 1000

		# Detect elements with JavaScript click event listeners (without mutating DOM)
		# On heavy pages (>10k elements) the querySelectorAll('*') + getEventListeners()
		# loop plus per-element DOM.describeNode CDP calls can take 10s+.
		# The JS expression below bails out early if the page is too heavy.
		# Elements are still detected via the accessibility tree and ClickableElementDetector.
		start_js_listener_detection = time.time()
		js_click_listener_backend_ids: set[int] = set()
		try:
			# Step 1: Run JS to find elements with click listeners and return them by reference
			js_listener_result = await cdp_session.cdp_client.send.Runtime.evaluate(
				params={
					'expression': """
					(() => {
						// getEventListeners is only available in DevTools context via includeCommandLineAPI
						if (typeof getEventListeners !== 'function') {
							return null;
						}

						const allElements = document.querySelectorAll('*');

						// Skip on heavy pages — listener detection is too expensive
						if (allElements.length > 10000) {
							return null;
						}

						const elementsWithListeners = [];

						for (const el of allElements) {
							try {
								const listeners = getEventListeners(el);
								// Check for click-related event listeners
								if (listeners.click || listeners.mousedown || listeners.mouseup || listeners.pointerdown || listeners.pointerup) {
									elementsWithListeners.push(el);
								}
							} catch (e) {
								// Ignore errors for individual elements (e.g., cross-origin)
							}
						}

						return elementsWithListeners;
					})()
					""",
					'includeCommandLineAPI': True,  # enables getEventListeners()
					'returnByValue': False,  # Return object references, not values
				},
				session_id=cdp_session.session_id,
			)

			result_object_id = js_listener_result.get('result', {}).get('objectId')
			if result_object_id:
				# Step 2: Get array properties to access each element
				array_props = await cdp_session.cdp_client.send.Runtime.getProperties(
					params={
						'objectId': result_object_id,
						'ownProperties': True,
					},
					session_id=cdp_session.session_id,
				)

				# Step 3: For each element, get its backend node ID via DOM.describeNode
				element_object_ids: list[str] = []
				for prop in array_props.get('result', []):
					# Array indices are numeric property names
					prop_name = prop.get('name', '') if isinstance(prop, dict) else ''
					if isinstance(prop_name, str) and prop_name.isdigit():
						prop_value = prop.get('value', {}) if isinstance(prop, dict) else {}
						if isinstance(prop_value, dict):
							object_id = prop_value.get('objectId')
							if object_id and isinstance(object_id, str):
								element_object_ids.append(object_id)

				# Batch resolve backend node IDs (run in parallel)
				async def get_backend_node_id(object_id: str) -> int | None:
					try:
						node_info = await cdp_session.cdp_client.send.DOM.describeNode(
							params={'objectId': object_id},
							session_id=cdp_session.session_id,
						)
						return node_info.get('node', {}).get('backendNodeId')
					except Exception:
						return None

				# Resolve all element object IDs to backend node IDs in parallel
				backend_ids = await asyncio.gather(*[get_backend_node_id(oid) for oid in element_object_ids])
				js_click_listener_backend_ids = {bid for bid in backend_ids if bid is not None}

				# Release the array object to avoid memory leaks
				try:
					await cdp_session.cdp_client.send.Runtime.releaseObject(
						params={'objectId': result_object_id},
						session_id=cdp_session.session_id,
					)
				except Exception:
					pass  # Best effort cleanup

				self.logger.debug(f'Detected {len(js_click_listener_backend_ids)} elements with JS click listeners')
		except Exception as e:
			self.logger.debug(f'Failed to detect JS event listeners: {e}')
		js_listener_detection_ms = (time.time() - start_js_listener_detection) * 1000

		# Define CDP request factories to avoid duplication
		def create_snapshot_request():
			return cdp_session.cdp_client.send.DOMSnapshot.captureSnapshot(
				params={
					'computedStyles': REQUIRED_COMPUTED_STYLES,
					'includePaintOrder': True,
					'includeDOMRects': True,
					'includeBlendedBackgroundColors': False,
					'includeTextColorOpacities': False,
				},
				session_id=cdp_session.session_id,
			)

		def create_dom_tree_request():
			return cdp_session.cdp_client.send.DOM.getDocument(
				params={'depth': -1, 'pierce': True}, session_id=cdp_session.session_id
			)

		start_cdp_calls = time.time()

		# Create initial tasks
		tasks = {
			'snapshot': create_task_with_error_handling(create_snapshot_request(), name='get_snapshot'),
			'dom_tree': create_task_with_error_handling(create_dom_tree_request(), name='get_dom_tree'),
			'ax_tree': create_task_with_error_handling(self._get_ax_tree_for_all_frames(target_id), name='get_ax_tree'),
			'device_pixel_ratio': create_task_with_error_handling(self._get_viewport_ratio(target_id), name='get_viewport_ratio'),
		}

		# Wait for all tasks with timeout
		done, pending = await asyncio.wait(tasks.values(), timeout=10.0)

		# Retry any failed or timed out tasks
		if pending:
			for task in pending:
				task.cancel()

			# Retry mapping for pending tasks
			retry_map = {
				tasks['snapshot']: lambda: create_task_with_error_handling(create_snapshot_request(), name='get_snapshot_retry'),
				tasks['dom_tree']: lambda: create_task_with_error_handling(create_dom_tree_request(), name='get_dom_tree_retry'),
				tasks['ax_tree']: lambda: create_task_with_error_handling(
					self._get_ax_tree_for_all_frames(target_id), name='get_ax_tree_retry'
				),
				tasks['device_pixel_ratio']: lambda: create_task_with_error_handling(
					self._get_viewport_ratio(target_id), name='get_viewport_ratio_retry'
				),
			}

			# Create new tasks only for the ones that didn't complete
			for key, task in tasks.items():
				if task in pending and task in retry_map:
					tasks[key] = retry_map[task]()

			# Wait again with shorter timeout
			done2, pending2 = await asyncio.wait([t for t in tasks.values() if not t.done()], timeout=2.0)

			if pending2:
				for task in pending2:
					task.cancel()

		# Extract results, tracking which ones failed
		results = {}
		failed = []
		for key, task in tasks.items():
			if task.done() and not task.cancelled():
				try:
					results[key] = task.result()
				except Exception as e:
					self.logger.warning(f'CDP request {key} failed with exception: {e}')
					failed.append(key)
			else:
				self.logger.warning(f'CDP request {key} timed out')
				failed.append(key)

		# If any required tasks failed, raise an exception
		if failed:
			raise TimeoutError(f'CDP requests failed or timed out: {", ".join(failed)}')

		snapshot = results['snapshot']
		dom_tree = results['dom_tree']
		ax_tree = results['ax_tree']
		device_pixel_ratio = results['device_pixel_ratio']
		end_cdp_calls = time.time()
		cdp_calls_ms = (end_cdp_calls - start_cdp_calls) * 1000

		# Calculate total time for _get_all_trees and overhead
		start_snapshot_processing = time.time()

		# DEBUG: Log snapshot info and limit documents to prevent explosion
		if snapshot and 'documents' in snapshot:
			original_doc_count = len(snapshot['documents'])
			# Limit to max_iframes documents to prevent iframe explosion
			if original_doc_count > self.max_iframes:
				self.logger.warning(
					f'⚠️ Limiting processing of {original_doc_count} iframes on page to only first {self.max_iframes} to prevent crashes!'
				)
				snapshot['documents'] = snapshot['documents'][: self.max_iframes]

			total_nodes = sum(len(doc.get('nodes', [])) for doc in snapshot['documents'])
			self.logger.debug(f'🔍 DEBUG: Snapshot contains {len(snapshot["documents"])} frames with {total_nodes} total nodes')
			# Log iframe-specific info
			for doc_idx, doc in enumerate(snapshot['documents']):
				if doc_idx > 0:  # Not the main document
					self.logger.debug(
						f'🔍 DEBUG: Iframe #{doc_idx} {doc.get("frameId", "no-frame-id")} {doc.get("url", "no-url")} has {len(doc.get("nodes", []))} nodes'
					)

		snapshot_processing_ms = (time.time() - start_snapshot_processing) * 1000

		# Return with detailed timing breakdown
		return TargetAllTrees(
			snapshot=snapshot,
			dom_tree=dom_tree,
			ax_tree=ax_tree,
			device_pixel_ratio=device_pixel_ratio,
			cdp_timing={
				'iframe_scroll_detection_ms': iframe_scroll_ms,
				'js_listener_detection_ms': js_listener_detection_ms,
				'cdp_parallel_calls_ms': cdp_calls_ms,
				'snapshot_processing_ms': snapshot_processing_ms,
			},
			js_click_listener_backend_ids=js_click_listener_backend_ids if js_click_listener_backend_ids else None,
		)