def __init__(
		self,
		task: str,
		llm: BaseChatModel | None = None,
		# Optional parameters
		browser_profile: BrowserProfile | None = None,
		browser_session: BrowserSession | None = None,
		browser: Browser | None = None,  # Alias for browser_session
		tools: Tools[Context] | None = None,
		controller: Tools[Context] | None = None,  # Alias for tools
		# Skills integration
		skill_ids: list[str | Literal['*']] | None = None,
		skills: list[str | Literal['*']] | None = None,  # Alias for skill_ids
		skill_service: Any | None = None,
		# Initial agent run parameters
		sensitive_data: dict[str, str | dict[str, str]] | None = None,
		initial_actions: list[dict[str, dict[str, Any]]] | None = None,
		# Cloud Callbacks
		register_new_step_callback: (
			Callable[['BrowserStateSummary', 'AgentOutput', int], None]  # Sync callback
			| Callable[['BrowserStateSummary', 'AgentOutput', int], Awaitable[None]]  # Async callback
			| None
		) = None,
		register_done_callback: (
			Callable[['AgentHistoryList'], Awaitable[None]]  # Async Callback
			| Callable[['AgentHistoryList'], None]  # Sync Callback
			| None
		) = None,
		register_external_agent_status_raise_error_callback: Callable[[], Awaitable[bool]] | None = None,
		register_should_stop_callback: Callable[[], Awaitable[bool]] | None = None,
		# Agent settings
		output_model_schema: type[AgentStructuredOutput] | None = None,
		extraction_schema: dict | None = None,
		use_vision: bool | Literal['auto'] = True,
		save_conversation_path: str | Path | None = None,
		save_conversation_path_encoding: str | None = 'utf-8',
		max_failures: int = 5,
		override_system_message: str | None = None,
		extend_system_message: str | None = None,
		generate_gif: bool | str = False,
		available_file_paths: list[str] | None = None,
		include_attributes: list[str] | None = None,
		max_actions_per_step: int = 5,
		use_thinking: bool = True,
		flash_mode: bool = False,
		demo_mode: bool | None = None,
		max_history_items: int | None = None,
		page_extraction_llm: BaseChatModel | None = None,
		fallback_llm: BaseChatModel | None = None,
		use_judge: bool = True,
		ground_truth: str | None = None,
		judge_llm: BaseChatModel | None = None,
		injected_agent_state: AgentState | None = None,
		source: str | None = None,
		file_system_path: str | None = None,
		task_id: str | None = None,
		calculate_cost: bool = False,
		pricing_url: str | None = None,
		display_files_in_done_text: bool = True,
		include_tool_call_examples: bool = False,
		vision_detail_level: Literal['auto', 'low', 'high'] = 'auto',
		llm_timeout: int | None = None,
		step_timeout: int = 180,
		directly_open_url: bool = True,
		include_recent_events: bool = False,
		sample_images: list[ContentPartTextParam | ContentPartImageParam] | None = None,
		final_response_after_failure: bool = True,
		enable_planning: bool = True,
		planning_replan_on_stall: int = 3,
		planning_exploration_limit: int = 5,
		loop_detection_window: int = 20,
		loop_detection_enabled: bool = True,
		llm_screenshot_size: tuple[int, int] | None = None,
		message_compaction: MessageCompactionSettings | bool | None = True,
		max_clickable_elements_length: int = 40000,
		_url_shortening_limit: int = 25,
		enable_signal_handler: bool = True,
		**kwargs,
	):
		# Validate llm_screenshot_size
		if llm_screenshot_size is not None:
			if not isinstance(llm_screenshot_size, tuple) or len(llm_screenshot_size) != 2:
				raise ValueError('llm_screenshot_size must be a tuple of (width, height)')
			width, height = llm_screenshot_size
			if not isinstance(width, int) or not isinstance(height, int):
				raise ValueError('llm_screenshot_size dimensions must be integers')
			if width < 100 or height < 100:
				raise ValueError('llm_screenshot_size dimensions must be at least 100 pixels')
			self.logger.info(f'🖼️  LLM screenshot resizing enabled: {width}x{height}')
		if llm is None:
			default_llm_name = CONFIG.DEFAULT_LLM
			if default_llm_name:
				from browser_use.llm.models import get_llm_by_name

				llm = get_llm_by_name(default_llm_name)
			else:
				# No default LLM specified, use the original default
				from browser_use import ChatBrowserUse

				llm = ChatBrowserUse()

		# set flashmode = True if llm is ChatBrowserUse
		if llm.provider == 'browser-use':
			flash_mode = True

		# Flash mode strips plan fields from the output schema, so planning is structurally impossible
		if flash_mode:
			enable_planning = False

		# Auto-configure llm_screenshot_size for Claude Sonnet models
		if llm_screenshot_size is None:
			model_name = getattr(llm, 'model', '')
			if isinstance(model_name, str) and model_name.startswith('claude-sonnet'):
				llm_screenshot_size = (1400, 850)
				logger.info('🖼️  Auto-configured LLM screenshot size for Claude Sonnet: 1400x850')

		if page_extraction_llm is None:
			page_extraction_llm = llm
		if judge_llm is None:
			judge_llm = llm
		if available_file_paths is None:
			available_file_paths = []

		# Set timeout based on model name if not explicitly provided
		if llm_timeout is None:

			def _get_model_timeout(llm_model: BaseChatModel) -> int:
				"""Determine timeout based on model name"""
				model_name = getattr(llm_model, 'model', '').lower()
				if 'gemini' in model_name:
					if '3-pro' in model_name:
						return 90
					return 75
				elif 'groq' in model_name:
					return 30
				elif 'o3' in model_name or 'claude' in model_name or 'sonnet' in model_name or 'deepseek' in model_name:
					return 90
				else:
					return 75  # Default timeout

			llm_timeout = _get_model_timeout(llm)

		self.id = task_id or uuid7str()
		self.task_id: str = self.id
		self.session_id: str = uuid7str()

		base_profile = browser_profile or DEFAULT_BROWSER_PROFILE
		if base_profile is DEFAULT_BROWSER_PROFILE:
			base_profile = base_profile.model_copy()
		if demo_mode is not None and base_profile.demo_mode != demo_mode:
			base_profile = base_profile.model_copy(update={'demo_mode': demo_mode})
		browser_profile = base_profile

		# Handle browser vs browser_session parameter (browser takes precedence)
		if browser and browser_session:
			raise ValueError('Cannot specify both "browser" and "browser_session" parameters. Use "browser" for the cleaner API.')
		browser_session = browser or browser_session

		if browser_session is not None and demo_mode is not None and browser_session.browser_profile.demo_mode != demo_mode:
			browser_session.browser_profile = browser_session.browser_profile.model_copy(update={'demo_mode': demo_mode})

		self.browser_session = browser_session or BrowserSession(
			browser_profile=browser_profile,
			id=uuid7str()[:-4] + self.id[-4:],  # re-use the same 4-char suffix so they show up together in logs
		)

		self._demo_mode_enabled: bool = bool(self.browser_profile.demo_mode) if self.browser_session else False
		if self._demo_mode_enabled and getattr(self.browser_profile, 'headless', False):
			self.logger.warning(
				'Demo mode is enabled but the browser is headless=True; set headless=False to view the in-browser panel.'
			)

		# Initialize available file paths as direct attribute
		self.available_file_paths = available_file_paths

		# Set up tools first (needed to detect output_model_schema)
		if tools is not None:
			self.tools = tools
		elif controller is not None:
			self.tools = controller
		else:
			# Exclude screenshot tool when use_vision is not auto
			exclude_actions = ['screenshot'] if use_vision != 'auto' else []
			self.tools = Tools(exclude_actions=exclude_actions, display_files_in_done_text=display_files_in_done_text)

		# Enforce screenshot exclusion when use_vision != 'auto', even if user passed custom tools
		if use_vision != 'auto':
			self.tools.exclude_action('screenshot')

		# Enable coordinate clicking for models that support it
		model_name = getattr(llm, 'model', '').lower()
		supports_coordinate_clicking = any(
			pattern in model_name for pattern in ['claude-sonnet-4', 'claude-opus-4', 'gemini-3-pro', 'browser-use/']
		)
		if supports_coordinate_clicking:
			self.tools.set_coordinate_clicking(True)

		# Handle skills vs skill_ids parameter (skills takes precedence)
		if skills and skill_ids:
			raise ValueError('Cannot specify both "skills" and "skill_ids" parameters. Use "skills" for the cleaner API.')
		skill_ids = skills or skill_ids

		# Skills integration - use injected service or create from skill_ids
		self.skill_service = None
		self._skills_registered = False
		if skill_service is not None:
			self.skill_service = skill_service
		elif skill_ids:
			from browser_use.skills import SkillService

			self.skill_service = SkillService(skill_ids=skill_ids)

		# Structured output - use explicit param or detect from tools
		tools_output_model = self.tools.get_output_model()
		if output_model_schema is not None and tools_output_model is not None:
			# Both provided - warn if they differ
			if output_model_schema is not tools_output_model:
				logger.warning(
					f'output_model_schema ({output_model_schema.__name__}) differs from Tools output_model '
					f'({tools_output_model.__name__}). Using Agent output_model_schema.'
				)
		elif output_model_schema is None and tools_output_model is not None:
			# Only tools has it - use that (cast is safe: both are BaseModel subclasses)
			output_model_schema = cast(type[AgentStructuredOutput], tools_output_model)
		self.output_model_schema = output_model_schema
		if self.output_model_schema is not None:
			self.tools.use_structured_output_action(self.output_model_schema)

		# Extraction schema: explicit param takes priority, otherwise auto-bridge from output_model_schema
		self.extraction_schema = extraction_schema
		if self.extraction_schema is None and self.output_model_schema is not None:
			self.extraction_schema = self.output_model_schema.model_json_schema()

		# Core components - task enhancement now has access to output_model_schema from tools
		self.task = self._enhance_task_with_schema(task, output_model_schema)
		self.llm = llm
		self.judge_llm = judge_llm

		# Fallback LLM configuration
		self._fallback_llm: BaseChatModel | None = fallback_llm
		self._using_fallback_llm: bool = False
		self._original_llm: BaseChatModel = llm  # Store original for reference
		self.directly_open_url = directly_open_url
		self.include_recent_events = include_recent_events
		self._url_shortening_limit = _url_shortening_limit

		self.sensitive_data = sensitive_data

		self.sample_images = sample_images

		if isinstance(message_compaction, bool):
			message_compaction = MessageCompactionSettings(enabled=message_compaction)

		self.settings = AgentSettings(
			use_vision=use_vision,
			vision_detail_level=vision_detail_level,
			save_conversation_path=save_conversation_path,
			save_conversation_path_encoding=save_conversation_path_encoding,
			max_failures=max_failures,
			override_system_message=override_system_message,
			extend_system_message=extend_system_message,
			generate_gif=generate_gif,
			include_attributes=include_attributes,
			max_actions_per_step=max_actions_per_step,
			use_thinking=use_thinking,
			flash_mode=flash_mode,
			max_history_items=max_history_items,
			page_extraction_llm=page_extraction_llm,
			calculate_cost=calculate_cost,
			include_tool_call_examples=include_tool_call_examples,
			llm_timeout=llm_timeout,
			step_timeout=step_timeout,
			final_response_after_failure=final_response_after_failure,
			use_judge=use_judge,
			ground_truth=ground_truth,
			enable_planning=enable_planning,
			planning_replan_on_stall=planning_replan_on_stall,
			planning_exploration_limit=planning_exploration_limit,
			loop_detection_window=loop_detection_window,
			loop_detection_enabled=loop_detection_enabled,
			message_compaction=message_compaction,
			max_clickable_elements_length=max_clickable_elements_length,
		)

		# Token cost service
		self.token_cost_service = TokenCost(include_cost=calculate_cost, pricing_url=pricing_url)
		self.token_cost_service.register_llm(llm)
		self.token_cost_service.register_llm(page_extraction_llm)
		self.token_cost_service.register_llm(judge_llm)
		if self.settings.message_compaction and self.settings.message_compaction.compaction_llm:
			self.token_cost_service.register_llm(self.settings.message_compaction.compaction_llm)

		# Store signal handler setting (not part of AgentSettings as it's runtime behavior)
		self.enable_signal_handler = enable_signal_handler

		# Initialize state
		self.state = injected_agent_state or AgentState()

		# Configure loop detector window size from settings
		self.state.loop_detector.window_size = self.settings.loop_detection_window

		# Initialize history
		self.history = AgentHistoryList(history=[], usage=None)

		# Initialize agent directory
		import time

		timestamp = int(time.time())
		base_tmp = Path(tempfile.gettempdir())
		self.agent_directory = base_tmp / f'browser_use_agent_{self.id}_{timestamp}'

		# Initialize file system and screenshot service
		self._set_file_system(file_system_path)
		self._set_screenshot_service()

		# Action setup
		self._setup_action_models()
		self._set_browser_use_version_and_source(source)

		initial_url = None

		# only load url if no initial actions are provided
		if self.directly_open_url and not self.state.follow_up_task and not initial_actions:
			initial_url = self._extract_start_url(self.task)
			if initial_url:
				self.logger.info(f'🔗 Found URL in task: {initial_url}, adding as initial action...')
				initial_actions = [{'navigate': {'url': initial_url, 'new_tab': False}}]

		self.initial_url = initial_url

		self.initial_actions = self._convert_initial_actions(initial_actions) if initial_actions else None
		# Verify we can connect to the model
		self._verify_and_setup_llm()

		# TODO: move this logic to the LLMs
		# Handle users trying to use use_vision=True with DeepSeek models
		if 'deepseek' in self.llm.model.lower():
			self.logger.warning('⚠️ DeepSeek models do not support use_vision=True yet. Setting use_vision=False for now...')
			self.settings.use_vision = False

		# Handle users trying to use use_vision=True with XAI models that don't support it
		# grok-3 variants and grok-code don't support vision; grok-2 and grok-4 do
		model_lower = self.llm.model.lower()
		if 'grok-3' in model_lower or 'grok-code' in model_lower:
			self.logger.warning('⚠️ This XAI model does not support use_vision=True yet. Setting use_vision=False for now...')
			self.settings.use_vision = False

		logger.debug(
			f'{" +vision" if self.settings.use_vision else ""}'
			f' extraction_model={self.settings.page_extraction_llm.model if self.settings.page_extraction_llm else "Unknown"}'
			f'{" +file_system" if self.file_system else ""}'
		)

		# Store llm_screenshot_size in browser_session so tools can access it
		self.browser_session.llm_screenshot_size = llm_screenshot_size

		# Check if LLM is ChatAnthropic instance
		from browser_use.llm.anthropic.chat import ChatAnthropic

		is_anthropic = isinstance(self.llm, ChatAnthropic)

		# Check if model is a browser-use fine-tuned model (uses simplified prompts)
		is_browser_use_model = 'browser-use/' in self.llm.model.lower()

		# Initialize message manager with state
		# Initial system prompt with all actions - will be updated during each step
		self._message_manager = MessageManager(
			task=self.task,
			system_message=SystemPrompt(
				max_actions_per_step=self.settings.max_actions_per_step,
				override_system_message=override_system_message,
				extend_system_message=extend_system_message,
				use_thinking=self.settings.use_thinking,
				flash_mode=self.settings.flash_mode,
				is_anthropic=is_anthropic,
				is_browser_use_model=is_browser_use_model,
				model_name=self.llm.model,
			).get_system_message(),
			file_system=self.file_system,
			state=self.state.message_manager_state,
			use_thinking=self.settings.use_thinking,
			# Settings that were previously in MessageManagerSettings
			include_attributes=self.settings.include_attributes,
			sensitive_data=sensitive_data,
			max_history_items=self.settings.max_history_items,
			vision_detail_level=self.settings.vision_detail_level,
			include_tool_call_examples=self.settings.include_tool_call_examples,
			include_recent_events=self.include_recent_events,
			sample_images=self.sample_images,
			llm_screenshot_size=llm_screenshot_size,
			max_clickable_elements_length=self.settings.max_clickable_elements_length,
		)

		if self.sensitive_data:
			# Check if sensitive_data has domain-specific credentials
			has_domain_specific_credentials = any(isinstance(v, dict) for v in self.sensitive_data.values())

			# If no allowed_domains are configured, show a security warning
			if not self.browser_profile.allowed_domains:
				self.logger.warning(
					'⚠️ Agent(sensitive_data=••••••••) was provided but Browser(allowed_domains=[...]) is not locked down! ⚠️\n'
					'          ☠️ If the agent visits a malicious website and encounters a prompt-injection attack, your sensitive_data may be exposed!\n\n'
					'   \n'
				)

			# If we're using domain-specific credentials, validate domain patterns
			elif has_domain_specific_credentials:
				# For domain-specific format, ensure all domain patterns are included in allowed_domains
				domain_patterns = [k for k, v in self.sensitive_data.items() if isinstance(v, dict)]

				# Validate each domain pattern against allowed_domains
				for domain_pattern in domain_patterns:
					is_allowed = False
					for allowed_domain in self.browser_profile.allowed_domains:
						# Special cases that don't require URL matching
						if domain_pattern == allowed_domain or allowed_domain == '*':
							is_allowed = True
							break

						# Need to create example URLs to compare the patterns
						# Extract the domain parts, ignoring scheme
						pattern_domain = domain_pattern.split('://')[-1] if '://' in domain_pattern else domain_pattern
						allowed_domain_part = allowed_domain.split('://')[-1] if '://' in allowed_domain else allowed_domain

						# Check if pattern is covered by an allowed domain
						# Example: "google.com" is covered by "*.google.com"
						if pattern_domain == allowed_domain_part or (
							allowed_domain_part.startswith('*.')
							and (
								pattern_domain == allowed_domain_part[2:]
								or pattern_domain.endswith('.' + allowed_domain_part[2:])
							)
						):
							is_allowed = True
							break

					if not is_allowed:
						self.logger.warning(
							f'⚠️ Domain pattern "{domain_pattern}" in sensitive_data is not covered by any pattern in allowed_domains={self.browser_profile.allowed_domains}\n'
							f'   This may be a security risk as credentials could be used on unintended domains.'
						)

		# Callbacks
		self.register_new_step_callback = register_new_step_callback
		self.register_done_callback = register_done_callback
		self.register_should_stop_callback = register_should_stop_callback
		self.register_external_agent_status_raise_error_callback = register_external_agent_status_raise_error_callback

		# Telemetry
		self.telemetry = ProductTelemetry()

		# Event bus with WAL persistence
		# Default to ~/.config/browseruse/events/{agent_session_id}.jsonl
		# wal_path = CONFIG.BROWSER_USE_CONFIG_DIR / 'events' / f'{self.session_id}.jsonl'
		self.eventbus = EventBus(name=f'Agent_{str(self.id)[-4:]}')

		if self.settings.save_conversation_path:
			self.settings.save_conversation_path = Path(self.settings.save_conversation_path).expanduser().resolve()
			self.logger.info(f'💬 Saving conversation to {_log_pretty_path(self.settings.save_conversation_path)}')

		# Initialize download tracking
		assert self.browser_session is not None, 'BrowserSession is not set up'
		self.has_downloads_path = self.browser_session.browser_profile.downloads_path is not None
		if self.has_downloads_path:
			self._last_known_downloads: list[str] = []
			self.logger.debug('📁 Initialized download tracking for agent')

		# Event-based pause control (kept out of AgentState for serialization)
		self._external_pause_event = asyncio.Event()
		self._external_pause_event.set()