def create_history_gif(
	task: str,
	history: AgentHistoryList,
	#
	output_path: str = 'agent_history.gif',
	duration: int = 3000,
	show_goals: bool = True,
	show_task: bool = True,
	show_logo: bool = False,
	font_size: int = 40,
	title_font_size: int = 56,
	goal_font_size: int = 44,
	margin: int = 40,
	line_spacing: float = 1.5,
) -> None:
	"""Create a GIF from the agent's history with overlaid task and goal text."""
	if not history.history:
		logger.warning('No history to create GIF from')
		return

	from PIL import Image, ImageFont

	images = []

	# if history is empty, we can't create a gif
	if not history.history:
		logger.warning('No history to create GIF from')
		return

	# Get all screenshots from history (including None placeholders)
	screenshots = history.screenshots(return_none_if_not_screenshot=True)

	if not screenshots:
		logger.warning('No screenshots found in history')
		return

	# Find the first non-placeholder screenshot
	# A screenshot is considered a placeholder if:
	# 1. It's the exact 4px placeholder for about:blank pages, OR
	# 2. It comes from a new tab page (chrome://newtab/, about:blank, etc.)
	first_real_screenshot = None
	for screenshot in screenshots:
		if screenshot and screenshot != PLACEHOLDER_4PX_SCREENSHOT:
			first_real_screenshot = screenshot
			break

	if not first_real_screenshot:
		logger.warning('No valid screenshots found (all are placeholders or from new tab pages)')
		return

	# Try to load nicer fonts
	try:
		# Try different font options in order of preference
		# ArialUni is a font that comes with Office and can render most non-alphabet characters
		font_options = [
			'PingFang',
			'STHeiti Medium',
			'Microsoft YaHei',  # 微软雅黑
			'SimHei',  # 黑体
			'SimSun',  # 宋体
			'Noto Sans CJK SC',  # 思源黑体
			'WenQuanYi Micro Hei',  # 文泉驿微米黑
			'Helvetica',
			'Arial',
			'DejaVuSans',
			'Verdana',
		]
		font_loaded = False

		for font_name in font_options:
			try:
				if platform.system() == 'Windows':
					# Need to specify the abs font path on Windows
					font_name = os.path.join(CONFIG.WIN_FONT_DIR, font_name + '.ttf')
				regular_font = ImageFont.truetype(font_name, font_size)
				title_font = ImageFont.truetype(font_name, title_font_size)
				font_loaded = True
				break
			except OSError:
				continue

		if not font_loaded:
			raise OSError('No preferred fonts found')

	except OSError:
		regular_font = ImageFont.load_default()
		title_font = ImageFont.load_default()

	# Load logo if requested
	logo = None
	if show_logo:
		try:
			logo = Image.open('./static/browser-use.png')
			# Resize logo to be small (e.g., 40px height)
			logo_height = 150
			aspect_ratio = logo.width / logo.height
			logo_width = int(logo_height * aspect_ratio)
			logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
		except Exception as e:
			logger.warning(f'Could not load logo: {e}')

	# Create task frame if requested
	if show_task and task:
		# Find the first non-placeholder screenshot for the task frame
		first_real_screenshot = None
		for item in history.history:
			screenshot_b64 = item.state.get_screenshot()
			if screenshot_b64 and screenshot_b64 != PLACEHOLDER_4PX_SCREENSHOT:
				first_real_screenshot = screenshot_b64
				break

		if first_real_screenshot:
			task_frame = _create_task_frame(
				task,
				first_real_screenshot,
				title_font,  # type: ignore
				regular_font,  # type: ignore
				logo,
				line_spacing,
			)
			images.append(task_frame)
		else:
			logger.warning('No real screenshots found for task frame, skipping task frame')

	# Process each history item with its corresponding screenshot
	for i, (item, screenshot) in enumerate(zip(history.history, screenshots), 1):
		if not screenshot:
			continue

		# Skip placeholder screenshots from about:blank pages
		# These are 4x4 white PNGs encoded as a specific base64 string
		if screenshot == PLACEHOLDER_4PX_SCREENSHOT:
			logger.debug(f'Skipping placeholder screenshot from about:blank page at step {i}')
			continue

		# Skip screenshots from new tab pages
		from browser_use.utils import is_new_tab_page

		if is_new_tab_page(item.state.url):
			logger.debug(f'Skipping screenshot from new tab page ({item.state.url}) at step {i}')
			continue

		# Convert base64 screenshot to PIL Image
		img_data = base64.b64decode(screenshot)
		image = Image.open(io.BytesIO(img_data))

		if show_goals and item.model_output:
			image = _add_overlay_to_image(
				image=image,
				step_number=i,
				goal_text=item.model_output.current_state.next_goal,
				regular_font=regular_font,  # type: ignore
				title_font=title_font,  # type: ignore
				margin=margin,
				logo=logo,
			)

		images.append(image)

	if images:
		# Save the GIF
		images[0].save(
			output_path,
			save_all=True,
			append_images=images[1:],
			duration=duration,
			loop=0,
			optimize=False,
		)
		logger.info(f'Created GIF at {output_path}')
	else:
		logger.warning('No images found in history to create GIF')