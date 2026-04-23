def update_config_with_click_args(config: dict[str, Any], ctx: click.Context) -> dict[str, Any]:
	"""Update configuration with command-line arguments."""
	# Ensure required sections exist
	if 'model' not in config:
		config['model'] = {}
	if 'browser' not in config:
		config['browser'] = {}

	# Update configuration with command-line args if provided
	if ctx.params.get('model'):
		config['model']['name'] = ctx.params['model']
	if ctx.params.get('headless') is not None:
		config['browser']['headless'] = ctx.params['headless']
	if ctx.params.get('window_width'):
		config['browser']['window_width'] = ctx.params['window_width']
	if ctx.params.get('window_height'):
		config['browser']['window_height'] = ctx.params['window_height']
	if ctx.params.get('user_data_dir'):
		config['browser']['user_data_dir'] = ctx.params['user_data_dir']
	if ctx.params.get('profile_directory'):
		config['browser']['profile_directory'] = ctx.params['profile_directory']
	if ctx.params.get('cdp_url'):
		config['browser']['cdp_url'] = ctx.params['cdp_url']

	# Consolidated proxy dict
	proxy: dict[str, str] = {}
	if ctx.params.get('proxy_url'):
		proxy['server'] = ctx.params['proxy_url']
	if ctx.params.get('no_proxy'):
		# Store as comma-separated list string to match Chrome flag
		proxy['bypass'] = ','.join([p.strip() for p in ctx.params['no_proxy'].split(',') if p.strip()])
	if ctx.params.get('proxy_username'):
		proxy['username'] = ctx.params['proxy_username']
	if ctx.params.get('proxy_password'):
		proxy['password'] = ctx.params['proxy_password']
	if proxy:
		config['browser']['proxy'] = proxy

	return config