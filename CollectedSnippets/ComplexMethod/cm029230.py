async def multi_act(self, actions: list[ActionModel]) -> list[ActionResult]:
		"""Execute multiple actions with page-change guards.

		Two layers of protection prevent executing actions against stale DOM:
		  1. Static flag: actions tagged with terminates_sequence=True (navigate, search, go_back, switch)
		     automatically abort remaining queued actions.
		  2. Runtime detection: after every action, the current URL and focused target are compared
		     to pre-action values. Any change aborts the remaining queue.
		"""
		results: list[ActionResult] = []
		total_actions = len(actions)

		assert self.browser_session is not None, 'BrowserSession is not set up'
		try:
			if (
				self.browser_session._cached_browser_state_summary is not None
				and self.browser_session._cached_browser_state_summary.dom_state is not None
			):
				cached_selector_map = dict(self.browser_session._cached_browser_state_summary.dom_state.selector_map)
			else:
				cached_selector_map = {}
		except Exception as e:
			self.logger.error(f'Error getting cached selector map: {e}')
			cached_selector_map = {}

		for i, action in enumerate(actions):
			# Get action name from the action model BEFORE try block to ensure it's always available in except
			action_data = action.model_dump(exclude_unset=True)
			action_name = next(iter(action_data.keys())) if action_data else 'unknown'

			if i > 0:
				# ONLY ALLOW TO CALL `done` IF IT IS A SINGLE ACTION
				if action_data.get('done') is not None:
					msg = f'Done action is allowed only as a single action - stopped after action {i} / {total_actions}.'
					self.logger.debug(msg)
					break

			# wait between actions (only after first action)
			if i > 0:
				self.logger.debug(f'Waiting {self.browser_profile.wait_between_actions} seconds between actions')
				await asyncio.sleep(self.browser_profile.wait_between_actions)

			try:
				await self._check_stop_or_pause()

				# Log action before execution
				await self._log_action(action, action_name, i + 1, total_actions)

				# Capture pre-action state for runtime page-change detection
				pre_action_url = await self.browser_session.get_current_page_url()
				pre_action_focus = self.browser_session.agent_focus_target_id

				result = await self.tools.act(
					action=action,
					browser_session=self.browser_session,
					file_system=self.file_system,
					page_extraction_llm=self.settings.page_extraction_llm,
					sensitive_data=self.sensitive_data,
					available_file_paths=self.available_file_paths,
					extraction_schema=self.extraction_schema,
				)

				if result.error:
					await self._demo_mode_log(
						f'Action "{action_name}" failed: {result.error}',
						'error',
						{'action': action_name, 'step': self.state.n_steps},
					)
				elif result.is_done:
					completion_text = result.long_term_memory or result.extracted_content or 'Task marked as done.'
					level = 'success' if result.success is not False else 'warning'
					await self._demo_mode_log(
						completion_text,
						level,
						{'action': action_name, 'step': self.state.n_steps},
					)

				results.append(result)

				if results[-1].is_done or results[-1].error or i == total_actions - 1:
					break

				# --- Page-change guards (only when more actions remain) ---

				# Layer 1: Static flag — action metadata declares it changes the page
				registered_action = self.tools.registry.registry.actions.get(action_name)
				if registered_action and registered_action.terminates_sequence:
					self.logger.info(
						f'Action "{action_name}" terminates sequence — skipping {total_actions - i - 1} remaining action(s)'
					)
					break

				# Layer 2: Runtime detection — URL or focus target changed
				post_action_url = await self.browser_session.get_current_page_url()
				post_action_focus = self.browser_session.agent_focus_target_id

				if post_action_url != pre_action_url or post_action_focus != pre_action_focus:
					self.logger.info(f'Page changed after "{action_name}" — skipping {total_actions - i - 1} remaining action(s)')
					break

			except Exception as e:
				# Handle any exceptions during action execution
				self.logger.error(f'❌ Executing action {i + 1} failed -> {type(e).__name__}: {e}')
				await self._demo_mode_log(
					f'Action "{action_name}" raised {type(e).__name__}: {e}',
					'error',
					{'action': action_name, 'step': self.state.n_steps},
				)
				raise e

		return results