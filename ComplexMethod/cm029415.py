async def execute_action(
		self,
		action_name: str,
		params: dict,
		browser_session: BrowserSession | None = None,
		page_extraction_llm: BaseChatModel | None = None,
		file_system: FileSystem | None = None,
		sensitive_data: dict[str, str | dict[str, str]] | None = None,
		available_file_paths: list[str] | None = None,
		extraction_schema: dict | None = None,
	) -> Any:
		"""Execute a registered action with simplified parameter handling"""
		if action_name not in self.registry.actions:
			raise ValueError(f'Action {action_name} not found')

		action = self.registry.actions[action_name]
		try:
			# Create the validated Pydantic model
			try:
				validated_params = action.param_model(**params)
			except Exception as e:
				raise ValueError(f'Invalid parameters {params} for action {action_name}: {type(e)}: {e}') from e

			if sensitive_data:
				# Get current URL if browser_session is provided
				current_url = None
				if browser_session and browser_session.agent_focus_target_id:
					try:
						# Get current page info from session_manager
						target = browser_session.session_manager.get_target(browser_session.agent_focus_target_id)
						if target:
							current_url = target.url
					except Exception:
						pass
				validated_params = self._replace_sensitive_data(validated_params, sensitive_data, current_url)

			# Build special context dict
			special_context = {
				'browser_session': browser_session,
				'page_extraction_llm': page_extraction_llm,
				'available_file_paths': available_file_paths,
				'has_sensitive_data': action_name == 'input' and bool(sensitive_data),
				'file_system': file_system,
				'extraction_schema': extraction_schema,
			}

			# Only pass sensitive_data to actions that explicitly need it (input)
			if action_name == 'input':
				special_context['sensitive_data'] = sensitive_data

			# Add CDP-related parameters if browser_session is available
			if browser_session:
				# Add page_url
				try:
					special_context['page_url'] = await browser_session.get_current_page_url()
				except Exception:
					special_context['page_url'] = None

				# Add cdp_client
				special_context['cdp_client'] = browser_session.cdp_client

			# All functions are now normalized to accept kwargs only
			# Call with params and unpacked special context
			try:
				return await action.function(params=validated_params, **special_context)
			except Exception as e:
				raise

		except ValueError as e:
			# Preserve ValueError messages from validation
			if 'requires browser_session but none provided' in str(e) or 'requires page_extraction_llm but none provided' in str(
				e
			):
				raise RuntimeError(str(e)) from e
			else:
				raise RuntimeError(f'Error executing action {action_name}: {str(e)}') from e
		except TimeoutError as e:
			raise RuntimeError(f'Error executing action {action_name} due to timeout.') from e
		except Exception as e:
			raise RuntimeError(f'Error executing action {action_name}: {str(e)}') from e