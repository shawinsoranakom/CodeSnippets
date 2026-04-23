async def cdp_client_for_node(self, node: EnhancedDOMTreeNode) -> CDPSession:
		"""Get CDP client for a specific DOM node based on its frame.

		IMPORTANT: backend_node_id is only valid in the session where the DOM was captured.
		We trust the node's session_id/frame_id/target_id instead of searching all sessions.
		"""

		# Strategy 1: If node has session_id, try to use that exact session (most specific)
		if node.session_id and self.session_manager:
			try:
				# Find the CDP session by session_id from SessionManager
				cdp_session = self.session_manager.get_session(node.session_id)
				if cdp_session:
					# Get target to log URL
					target = self.session_manager.get_target(cdp_session.target_id)
					self.logger.debug(f'✅ Using session from node.session_id for node {node.backend_node_id}: {target.url}')
					return cdp_session
			except Exception as e:
				self.logger.debug(f'Failed to get session by session_id {node.session_id}: {e}')

		# Strategy 2: If node has frame_id, use that frame's session
		if node.frame_id:
			try:
				cdp_session = await self.cdp_client_for_frame(node.frame_id)
				target = self.session_manager.get_target(cdp_session.target_id)
				self.logger.debug(f'✅ Using session from node.frame_id for node {node.backend_node_id}: {target.url}')
				return cdp_session
			except Exception as e:
				self.logger.debug(f'Failed to get session for frame {node.frame_id}: {e}')

		# Strategy 3: If node has target_id, use that target's session
		if node.target_id:
			try:
				cdp_session = await self.get_or_create_cdp_session(target_id=node.target_id, focus=False)
				target = self.session_manager.get_target(cdp_session.target_id)
				self.logger.debug(f'✅ Using session from node.target_id for node {node.backend_node_id}: {target.url}')
				return cdp_session
			except Exception as e:
				self.logger.debug(f'Failed to get session for target {node.target_id}: {e}')

		# Strategy 4: Fallback to agent_focus_target_id (the page where agent is currently working)
		if self.agent_focus_target_id:
			target = self.session_manager.get_target(self.agent_focus_target_id)
			try:
				# Use safe API with focus=False to avoid changing focus
				cdp_session = await self.get_or_create_cdp_session(self.agent_focus_target_id, focus=False)
				if target:
					self.logger.warning(
						f'⚠️ Node {node.backend_node_id} has no session/frame/target info. Using agent_focus session: {target.url}'
					)
				return cdp_session
			except ValueError:
				pass  # Fall through to last resort

		# Last resort: use main session
		self.logger.error(f'❌ No session info for node {node.backend_node_id} and no agent_focus available. Using main session.')
		return await self.get_or_create_cdp_session()