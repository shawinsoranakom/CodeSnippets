def __init__(
		self,
		# Core configuration
		id: str | None = None,
		cdp_url: str | None = None,
		is_local: bool = False,
		browser_profile: BrowserProfile | None = None,
		# Cloud browser params (don't mix with local browser params)
		cloud_profile_id: UUID | str | None = None,
		cloud_proxy_country_code: ProxyCountryCode | None = None,
		cloud_timeout: int | None = None,
		# Backward compatibility aliases for cloud params
		profile_id: UUID | str | None = None,
		proxy_country_code: ProxyCountryCode | None = None,
		timeout: int | None = None,
		# BrowserProfile fields that can be passed directly
		# From BrowserConnectArgs
		headers: dict[str, str] | None = None,
		# From BrowserLaunchArgs
		env: dict[str, str | float | bool] | None = None,
		executable_path: str | Path | None = None,
		headless: bool | None = None,
		args: list[str] | None = None,
		ignore_default_args: list[str] | Literal[True] | None = None,
		channel: str | None = None,
		chromium_sandbox: bool | None = None,
		devtools: bool | None = None,
		downloads_path: str | Path | None = None,
		traces_dir: str | Path | None = None,
		# From BrowserContextArgs
		accept_downloads: bool | None = None,
		permissions: list[str] | None = None,
		user_agent: str | None = None,
		screen: dict | None = None,
		viewport: dict | None = None,
		no_viewport: bool | None = None,
		device_scale_factor: float | None = None,
		record_har_content: str | None = None,
		record_har_mode: str | None = None,
		record_har_path: str | Path | None = None,
		record_video_dir: str | Path | None = None,
		record_video_framerate: int | None = None,
		record_video_size: dict | None = None,
		# From BrowserLaunchPersistentContextArgs
		user_data_dir: str | Path | None = None,
		# From BrowserNewContextArgs
		storage_state: str | Path | dict[str, Any] | None = None,
		# BrowserProfile specific fields
		## Cloud Browser Fields
		use_cloud: bool | None = None,
		cloud_browser: bool | None = None,  # Backward compatibility alias
		cloud_browser_params: CloudBrowserParams | None = None,
		## Other params
		disable_security: bool | None = None,
		deterministic_rendering: bool | None = None,
		allowed_domains: list[str] | None = None,
		prohibited_domains: list[str] | None = None,
		keep_alive: bool | None = None,
		proxy: ProxySettings | None = None,
		enable_default_extensions: bool | None = None,
		captcha_solver: bool | None = None,
		window_size: dict | None = None,
		window_position: dict | None = None,
		minimum_wait_page_load_time: float | None = None,
		wait_for_network_idle_page_load_time: float | None = None,
		wait_between_actions: float | None = None,
		filter_highlight_ids: bool | None = None,
		auto_download_pdfs: bool | None = None,
		profile_directory: str | None = None,
		cookie_whitelist_domains: list[str] | None = None,
		# DOM extraction layer configuration
		cross_origin_iframes: bool | None = None,
		highlight_elements: bool | None = None,
		dom_highlight_elements: bool | None = None,
		paint_order_filtering: bool | None = None,
		# Iframe processing limits
		max_iframes: int | None = None,
		max_iframe_depth: int | None = None,
	):
		# Following the same pattern as AgentSettings in service.py
		# Only pass non-None values to avoid validation errors
		profile_kwargs = {
			k: v
			for k, v in locals().items()
			if k
			not in [
				'self',
				'browser_profile',
				'id',
				'cloud_profile_id',
				'cloud_proxy_country_code',
				'cloud_timeout',
				'profile_id',
				'proxy_country_code',
				'timeout',
			]
			and v is not None
		}

		# Handle backward compatibility: prefer cloud_* params over old names
		final_profile_id = cloud_profile_id if cloud_profile_id is not None else profile_id
		final_proxy_country_code = cloud_proxy_country_code if cloud_proxy_country_code is not None else proxy_country_code
		final_timeout = cloud_timeout if cloud_timeout is not None else timeout

		# If any cloud params are provided, create cloud_browser_params
		if final_profile_id is not None or final_proxy_country_code is not None or final_timeout is not None:
			cloud_params = CreateBrowserRequest(
				cloud_profile_id=final_profile_id,
				cloud_proxy_country_code=final_proxy_country_code,
				cloud_timeout=final_timeout,
			)
			profile_kwargs['cloud_browser_params'] = cloud_params
			profile_kwargs['use_cloud'] = True

		# Handle backward compatibility: map cloud_browser to use_cloud
		if 'cloud_browser' in profile_kwargs:
			profile_kwargs['use_cloud'] = profile_kwargs.pop('cloud_browser')

		# If cloud_browser_params is set, force use_cloud=True
		if cloud_browser_params is not None:
			profile_kwargs['use_cloud'] = True

		# if is_local is False but executable_path is provided, set is_local to True
		if is_local is False and executable_path is not None:
			profile_kwargs['is_local'] = True
		# Only set is_local=True when cdp_url is missing if we're not using cloud browser
		# (cloud browser will provide cdp_url later)
		use_cloud = profile_kwargs.get('use_cloud') or profile_kwargs.get('cloud_browser')
		if not cdp_url and not use_cloud:
			profile_kwargs['is_local'] = True

		# Create browser profile from direct parameters or use provided one
		if browser_profile is not None:
			# Merge any direct kwargs into the provided browser_profile (direct kwargs take precedence)
			merged_kwargs = {**browser_profile.model_dump(exclude_unset=True), **profile_kwargs}
			resolved_browser_profile = BrowserProfile(**merged_kwargs)
		else:
			resolved_browser_profile = BrowserProfile(**profile_kwargs)

		# Initialize the Pydantic model
		super().__init__(
			id=id or str(uuid7str()),
			browser_profile=resolved_browser_profile,
		)