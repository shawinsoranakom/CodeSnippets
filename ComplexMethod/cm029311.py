async def _build_dom_tree_without_highlights(self, previous_state: SerializedDOMState | None = None) -> SerializedDOMState:
		"""Build DOM tree without injecting JavaScript highlights (for parallel execution)."""
		try:
			self.logger.debug('🔍 DOMWatchdog._build_dom_tree_without_highlights: STARTING DOM tree build')

			# Create or reuse DOM service
			if self._dom_service is None:
				self._dom_service = DomService(
					browser_session=self.browser_session,
					logger=self.logger,
					cross_origin_iframes=self.browser_session.browser_profile.cross_origin_iframes,
					paint_order_filtering=self.browser_session.browser_profile.paint_order_filtering,
					max_iframes=self.browser_session.browser_profile.max_iframes,
					max_iframe_depth=self.browser_session.browser_profile.max_iframe_depth,
				)

			# Get serialized DOM tree using the service
			self.logger.debug('🔍 DOMWatchdog._build_dom_tree_without_highlights: Calling DomService.get_serialized_dom_tree...')
			start = time.time()
			self.current_dom_state, self.enhanced_dom_tree, timing_info = await self._dom_service.get_serialized_dom_tree(
				previous_cached_state=previous_state,
			)
			end = time.time()
			total_time_ms = (end - start) * 1000
			self.logger.debug(
				'🔍 DOMWatchdog._build_dom_tree_without_highlights: ✅ DomService.get_serialized_dom_tree completed'
			)

			# Build hierarchical timing breakdown as single multi-line string
			timing_lines = [f'⏱️ Total DOM tree time: {total_time_ms:.2f}ms', '📊 Timing breakdown:']

			# get_all_trees breakdown
			get_all_trees_ms = timing_info.get('get_all_trees_total_ms', 0)
			if get_all_trees_ms > 0:
				timing_lines.append(f'  ├─ get_all_trees: {get_all_trees_ms:.2f}ms')
				iframe_scroll_ms = timing_info.get('iframe_scroll_detection_ms', 0)
				cdp_parallel_ms = timing_info.get('cdp_parallel_calls_ms', 0)
				snapshot_proc_ms = timing_info.get('snapshot_processing_ms', 0)
				if iframe_scroll_ms > 0.01:
					timing_lines.append(f'  │  ├─ iframe_scroll_detection: {iframe_scroll_ms:.2f}ms')
				if cdp_parallel_ms > 0.01:
					timing_lines.append(f'  │  ├─ cdp_parallel_calls: {cdp_parallel_ms:.2f}ms')
				if snapshot_proc_ms > 0.01:
					timing_lines.append(f'  │  └─ snapshot_processing: {snapshot_proc_ms:.2f}ms')

			# build_ax_lookup
			build_ax_ms = timing_info.get('build_ax_lookup_ms', 0)
			if build_ax_ms > 0.01:
				timing_lines.append(f'  ├─ build_ax_lookup: {build_ax_ms:.2f}ms')

			# build_snapshot_lookup
			build_snapshot_ms = timing_info.get('build_snapshot_lookup_ms', 0)
			if build_snapshot_ms > 0.01:
				timing_lines.append(f'  ├─ build_snapshot_lookup: {build_snapshot_ms:.2f}ms')

			# construct_enhanced_tree
			construct_tree_ms = timing_info.get('construct_enhanced_tree_ms', 0)
			if construct_tree_ms > 0.01:
				timing_lines.append(f'  ├─ construct_enhanced_tree: {construct_tree_ms:.2f}ms')

			# serialize_accessible_elements breakdown
			serialize_total_ms = timing_info.get('serialize_accessible_elements_total_ms', 0)
			if serialize_total_ms > 0.01:
				timing_lines.append(f'  ├─ serialize_accessible_elements: {serialize_total_ms:.2f}ms')
				create_simp_ms = timing_info.get('create_simplified_tree_ms', 0)
				paint_order_ms = timing_info.get('calculate_paint_order_ms', 0)
				optimize_ms = timing_info.get('optimize_tree_ms', 0)
				bbox_ms = timing_info.get('bbox_filtering_ms', 0)
				assign_idx_ms = timing_info.get('assign_interactive_indices_ms', 0)
				clickable_ms = timing_info.get('clickable_detection_time_ms', 0)

				if create_simp_ms > 0.01:
					timing_lines.append(f'  │  ├─ create_simplified_tree: {create_simp_ms:.2f}ms')
					if clickable_ms > 0.01:
						timing_lines.append(f'  │  │  └─ clickable_detection: {clickable_ms:.2f}ms')
				if paint_order_ms > 0.01:
					timing_lines.append(f'  │  ├─ calculate_paint_order: {paint_order_ms:.2f}ms')
				if optimize_ms > 0.01:
					timing_lines.append(f'  │  ├─ optimize_tree: {optimize_ms:.2f}ms')
				if bbox_ms > 0.01:
					timing_lines.append(f'  │  ├─ bbox_filtering: {bbox_ms:.2f}ms')
				if assign_idx_ms > 0.01:
					timing_lines.append(f'  │  └─ assign_interactive_indices: {assign_idx_ms:.2f}ms')

			# Overheads
			get_dom_overhead_ms = timing_info.get('get_dom_tree_overhead_ms', 0)
			serialize_overhead_ms = timing_info.get('serialization_overhead_ms', 0)
			get_serialized_overhead_ms = timing_info.get('get_serialized_dom_tree_overhead_ms', 0)

			if get_dom_overhead_ms > 0.1:
				timing_lines.append(f'  ├─ get_dom_tree_overhead: {get_dom_overhead_ms:.2f}ms')
			if serialize_overhead_ms > 0.1:
				timing_lines.append(f'  ├─ serialization_overhead: {serialize_overhead_ms:.2f}ms')
			if get_serialized_overhead_ms > 0.1:
				timing_lines.append(f'  └─ get_serialized_dom_tree_overhead: {get_serialized_overhead_ms:.2f}ms')

			# Calculate total tracked time for validation
			main_operations_ms = (
				get_all_trees_ms
				+ build_ax_ms
				+ build_snapshot_ms
				+ construct_tree_ms
				+ serialize_total_ms
				+ get_dom_overhead_ms
				+ serialize_overhead_ms
				+ get_serialized_overhead_ms
			)
			untracked_time_ms = total_time_ms - main_operations_ms

			if untracked_time_ms > 1.0:  # Only log if significant
				timing_lines.append(f'  ⚠️  untracked_time: {untracked_time_ms:.2f}ms')

			# Single log call with all timing info
			self.logger.debug('\n'.join(timing_lines))

			# Update selector map for other watchdogs
			self.logger.debug('🔍 DOMWatchdog._build_dom_tree_without_highlights: Updating selector maps...')
			self.selector_map = self.current_dom_state.selector_map
			# Update BrowserSession's cached selector map
			if self.browser_session:
				self.browser_session.update_cached_selector_map(self.selector_map)
			self.logger.debug(
				f'🔍 DOMWatchdog._build_dom_tree_without_highlights: ✅ Selector maps updated, {len(self.selector_map)} elements'
			)

			# Skip JavaScript highlighting injection - Python highlighting will be applied later
			self.logger.debug('🔍 DOMWatchdog._build_dom_tree_without_highlights: ✅ COMPLETED DOM tree build (no JS highlights)')
			return self.current_dom_state

		except Exception as e:
			self.logger.error(f'Failed to build DOM tree without highlights: {e}')
			self.event_bus.dispatch(
				BrowserErrorEvent(
					error_type='DOMBuildFailed',
					message=str(e),
				)
			)
			raise